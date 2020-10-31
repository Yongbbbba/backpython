# unit test

import config
import bcrypt
import json

import pytest
from sqlalchemy import create_engine, text
from app import create_app

# database 연결
database = create_engine(config.test_config["DB_URL"], encoding="utf-8", max_overflow=0)

# test app 생성
@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config["TESTING"] = True
    api = app.test_client()
    # test client 생성 ##flask의 test client 기능을 통해 엔드포인트에 가상의 HTTP 요청과 응답을 만들어내어, integration test도 같이 할 수 있다.

    return api


# test data create & delete
## test를 하려면 회원이 있어야하고, 로그인을 해야하고, access token도 생성해야함
### setup_function과 teerdown_function 사용
def setup_function():
    ## Create test user
    password = "test1234"
    hashed_password = bcrypt.hashpw(password.encode("UTF-8"), bcrypt.gensalt())
    new_users = [
        {
            "id": 1,
            "name": "김영찬",
            "email": "mono@gmail.com",
            "profile": "architect",
            "hashed_password": hashed_password
        },
        {
            "id": 2,
            "name": "김성우",
            "email": "actor_joker@naver.com",
            "profile": "actor",
            "hashed_password": hashed_password
        },
        {
            "id": 3,
            "name": "서정길",
            "email": "disco_arirang@naver.com",
            "profile": "editor",
            "hashed_password": hashed_password
        },
    ]

    database.execute(
        text(
            """
    INSERT INTO users 
    (id, name, email, profile, hashed_password)
    VALUES 
    (:id, :name, :email, :profile, :hashed_password)
    """
        ),
        new_users
    )

    ## user2의 tweet 미리 생성

    database.execute(
        text(
            """
    INSERT INTO tweets (user_id, tweet)
    VALUES (2, "Hello world!")
    """
        )
    )


def teardown_function():
    ## delete test user, 다른 테스트에 영향을 미치지 않기 위해 test user 관련 데이터 삭제
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    # truncate 구문은 외부키가 걸려있으면 실행되지 않기 때문에 일시적으로 외부키 비활성화
    database.execute(text("TRUNCATE users"))  # users 테이블 데이터 삭제
    database.execute(text("TRUNCATE tweets"))  # tweets 테이블 데이터 삭제
    database.execute(text("TRUNCATE users_follow_list"))  # users_follow_list 테이블 데이터 삭제
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))  # 다시 외부키 활성화


# ping endpoint test
def test_ping(api):
    resp = api.get("/ping")  # test client의 가상의 get 요청을 통해 받은 response
    assert b"pong" in resp.data  # response의 body에 pong이라는 응답이 있는지 확인, resp.data는 byte임


# login endpoint test
def test_login(api):
    ## 로그인
    resp = api.post("/login", data=json.dumps({"email": "mono@gmail.com", "password": "test1234"}),
        content_type = "application/json")

    assert b"access_token" in resp.data


# access token이 없이는 401 응답을 리턴하는지 확인
def test_unauthorized(api):
    resp = api.post(
        "/tweet",
        data=json.dumps({"tweet": "hello world"}),
        content_type="application/json"
    )

    assert resp.status_code == 401

    resp = api.post(
        "/follow", data=json.dumps({"follow": 2}), content_type="application/json"
    )

    assert resp.status_code == 401

    resp = api.post(
        "/unfollow", data=json.dumps({"unfollow": 2}), content_type="application/json"
    )

    assert resp.status_code == 401


# tweet endpoint test
def test_tweet(api):
    ## 로그인
    resp = api.post(
        "/login",
        data=json.dumps({"email": "mono@gmail.com", "password": "test1234"}),
        content_type="application/json"
    )

    resp_json = json.loads(resp.data.decode("utf-8"))
    access_token = resp_json["access_token"]

    ## tweet

    resp = api.post(
        "/tweet",
        data=json.dumps({"tweet": "hello world"}),
        content_type="application/json",
        headers={"Authorization": access_token}
    )

    assert resp.status_code == 200

    ## tweet 확인

    resp = api.get("/timeline/1")
    tweets = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert tweets == {
        "user_id": 1,
        "timeline": [{"user_id": 1, "tweet": "hello world"}]
    }


# follow endpoint test
def test_follow(api):
    # 로그인
    resp = api.post(
        "/login",
        data=json.dumps({"email": "mono@gmail.com", "password": "test1234"}),
        content_type="application/json"
    )

    resp_json = json.loads(resp.data.decode("utf-8"))
    access_token = resp_json["access_token"]

    # user2 follow 하기
    resp = api.post(
        "/follow",
        data=json.dumps({"follow": 2}),
        content_type="application/json",
        headers={"Authorization": access_token}
    )
    assert resp.status_code == 200

    ## user1의 타임라인에 user2의 tweet이 있는지 확인
    ## setup_function에서  user2의 tweet을 미리 생성해놨었음
    resp = api.get("/timeline/1")
    tweets = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert tweets == {
        "user_id": 1,
        "timeline": [{"user_id": 2, "tweet": "Hello world!"}]
    }


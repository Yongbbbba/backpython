import jwt
import bcrypt

from datetime import datetime, timedelta

class UserService:
    def __init__(self, user_dao, config):
        self.user_dao = user_dao
        self.config = config

    def create_new_user(self, new_user):
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode('UTF-8'), 
            bcrypt.gensalt()
        )

        new_user_id = self.user_dao.inser_user(new_user)

        return new_user_id

    def login(self, credential):
        email = credential['email']
        password = credential['password']

        # DB에서 해당 이메일의 user id와  password 가져오기
        user_credential = self.user_dao.get_user_id_and_password(email)

        # 입력된 비밀번호를 암호화하여 DB에 있는 암호화된 비밀번호와 비교
        ## authorized가 true인지 false인지 체크
        authorized = user_credential and bcrypt.checkpw(password.encode('UTF-8'), user_credential['hashed_password'].encode("UTF-8"))

        return authorized

    def generate_access_token(self, user_id):
        payload = {
            'user_id' : user_id,
            'exp' : datetime.utcnow() + timedelta(seconds= 60 * 60 * 24) # expiration은 24시간
        }

        token = jwt.encode(payload, self.config['JWT_SECRET_KEY'], 'HS256')

        return token.decode('UTF-8')

    def follow(self, user_id, follow_id):
        return self.user_dao.insert_follow(user_id, follow_id)

    def unfollow(self, user_id, unfollow_id):
        return self.user_dao.insert_unfollow(user_id, unfollow_id)

    def get_user_id_and_password(self, email):
        return self.user_dao.get_user_id_and_password(email)
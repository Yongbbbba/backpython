# view (presentation layer)
# __init__.py

import jwt

from flask import request, jsonify, current_app, Response, g, redirect
from flask.json import JSONEncoder
from functools import wraps

## Default JSONEncoder는 set 자료형을 JSON으로 변환할 수 없다. 
## 그래서 JSONEncoder를 상속하여 set 자료형을 list로 변환 후 json으로 변환할 수 있도록 한다 
class CustomJSONEncoder(JSONEncoder):
    def defualt(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self,obj)

##########decorator start###########
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except:
                payload = None
            
            if payload is None: return Response(status=401)

            user_id = payload['user_id']
            g.user_id = user_id
        else:
            return Response(status=401)
        
        return f(*args, **kwargs)
    return decorated_function
##########decorator end##########

#endpoint 구현 
#service layer를 인자로 받음
def create_endpoints(app,services):
    app.json_encoder = CustomJSONEncoder

    user_service = services.user_service
    tweet_service = services.tweet_service

    #health check endpoint
    @app.route('/ping', methods=['GET'])
    def ping():
        return "pong"

    @app.route('/sign-up', methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user = user_service.create_new_user(new_user)

        return jsonify(new_user)
    
    #홈으로 이동시 login 되어있으면 timeline 엔드포인트로, 되어있지 않으면 sign-up 엔드포인트로
    @app.route('/', methods=['GET'])
    @login_required
    def home():
        try:
            user_id= g.user_id
            return redirect('/timeline/<int:user_id>')
        except HTTPError:
            return redirect('/sign-up')

    @app.route('/login', methods=['POST'])
    def login():
        credential = request.json
        authorized = user_service.login(credential)

        if authorized:
            user_credential = user_service.get_user_id_and_password(credential['email'])
            user_id = user_credential['id']
            token = user_service.generate_access_token(user_id)

            return jsonify({
                'user_id' : user_id,
                'access_token' : token
            })

        else:
            return '', 401

    @app.route('/tweet', methods=['POST'])
    @login_required
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']
        user_id = g.user_id

        result = tweet_service.tweet(user_id, tweet)
        if result is None:
            return '300자를 초과했습니다', 400
    
    @app.route('/follow', methods=['POST'])
    @login_required
    def follow():
        payload = request.json
        user_id = g.user_id
        follow_id = payload['follow']

        user_service.follow(user_id, follow_id)

        return '',200

    @app.route('/unfollow', methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        user_id = g.user_id
        unfollow_id = payload['unfollow']

        user_service.unfollow(user_id, unfollow_id)

        return '', 200

    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        timeline = tweet_service.timeline(user_id)

        return jsonify({
            'user_id' : user_id,
            'timeline' : timeline
        })

    @app.route('/timeline', methods=['GET'])
    @login_required
    def user_timeline():
        timeline =tweet_service.timeline(g.user_id)

        return jsonify({
            'user_id' : user_id,
            'timeline' : timeline
        })

    

    


    



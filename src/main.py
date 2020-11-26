"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
from flask_jwt_simple import JWTManager, create_jwt, jwt_required, get_jwt_identity
#from models import Person


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# jwt_simple_config
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET')  # Change this!
jwt = JWTManager(app)

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


# Provide a method to create access tokens. The create_jwt()
# function is used to actually generate the token
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    params = request.get_json()
    email = params.get('email', None)
    password = params.get('password', None)

    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    specific_user = User.query.filter_by(
        email=email
    ).one_or_none()

    if isinstance(specific_user, User):
        if specific_user.password == password:
            response = {'jwt': create_jwt(identity=specific_user.id)}
            return jsonify(response), 200
        else:
            return jsonify({
                "msg" : "bad credentials"
            }), 400
    else:
        return jsonify({
            "msg" : "bad credentials"
        }), 400


@app.route('/signup', methods=['POST'])
def handle_singup():
    input_data = request.json
    

    if 'email' in input_data and 'password' in input_data:
        new_user = User(
            email=input_data['email'], 
            password=input_data['password']
        )

        db.session.add(new_user)
        try:
            db.session.commit()
            return jsonify(new_user.serialize()), 200
        except Exception as error:
            db.session.rollback()
            return jsonify(
                {"msg" : error}
            ), 500
    else:
        return jsonify({
            "msg" : "check your keys..."
        }), 500

# Protect a view with jwt_required, which requires a valid jwt
# to be present in the headers.
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    specific_user_id = get_jwt_identity()
    specific_user = User.query.filter_by(
        id = specific_user_id
    ).one_or_none()

    #specific_user = User.query.get(specific_user_id)
    if specific_user is None:
        return jsonify({
            'msg' : "user not found"
        }), 404
    else:
        return jsonify({
            'msg' : "Yay! You sent your token correctly so I know who you are",
            "user_data": specific_user.serialize()
        }), 200

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

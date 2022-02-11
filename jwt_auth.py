# flask imports
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid  # for public id
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps

# create flask app object
app = Flask(__name__)
# Config db
app.config.update(
    SECRET_KEY="topsecrete@$",
    SQLALCHEMY_DATABASE_URI='postgresql://postgres:12345678@localhost/postgres',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Create db object
db = SQLAlchemy(app)


# Database ORMs
class User(db.Model):
    __tablename__ = 'data1'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(200))
    type = db.Column(db.String(20))

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return f(current_user, *args, **kwargs)
    return decorated


# User Database Route
# this route sends back list of user info
@app.route('/user', methods=['GET'])
@token_required
def get_user_info(user):
    if user.type == 'user':
        output ={
            'id': user.id,
            'public_id': user.public_id,
            'name': user.name,
            'email': user.email,
            "password": user.password,
            'type': user.type
            }
        return jsonify({'users': output})
    else:
        return jsonify({
            'message': 'User type is invalid !!'
        }), 401


# Admin Database Route
# this route sends back list of user info
@app.route('/admin', methods=['GET'])
@token_required
def get_admin_info(user):
    output = []
    if user.type == 'admin':
        users = User.query.all()
        # User.query.filter_by(type="user").all()
        # converting the query objects
        # to list of jsons
        for user in users:
            # appending the user data json
            # to the response list
            output.append({
                'id': user.id,
                'public_id': user.public_id,
                'name': user.name,
                'email': user.email,
                "password": user.password,
                'type': user.type
            })
        return jsonify({'users': output})
    else:
        return jsonify({
            'message': 'User type is invalid !!'
        }), 401


# route for logging user in
@app.route('/login', methods=['POST'])
def login():
    # request data
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        # returns 401 if any email or / and password is missing
        return make_response(
            {"msg":'Please Enter the data for login'},
            401,
            {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
        )
    user = User.query.filter_by(email=data.get('email')).first()
    if not user:
        # returns 401 if user does not exist
        return make_response(
            {"msg":'User does not exist'},
            401,
            {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
        )
    if check_password_hash(user.password, data.get('password')):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp': datetime.utcnow() + timedelta(minutes=60)
        }, app.config['SECRET_KEY'])
        return make_response(jsonify({'token': token.decode('UTF-8')}), 201)
    # returns 403 if password is wrong
    return make_response(
        {"msg":'Wrong Password !!'},
        403,
        {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
    )


# signup route
@app.route('/signup', methods=['POST'])
def signup():
    # get data using request
    data = request.get_json()
    # gets name, email and password
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    type = data.get('type')
    # checking for existing user
    user = User.query.filter_by(email=email).first()
    if not user:
        # database ORM object
        user = User(
            public_id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=generate_password_hash(password),
            type=type
        )
        # insert user
        db.session.add(user)
        db.session.commit()
        res = [{"msg": "Successfully registered."}, {"Data": [data]}]
        return make_response(jsonify(res), 201)
    else:
        # returns 202 if user already exists
        return make_response(jsonify({"msg":'User already exists. Please Log in.'}), 202)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)

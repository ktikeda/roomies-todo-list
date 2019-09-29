from flask import request, jsonify
from roomies_todo_list import app, db
from .models import User, UserSchema
from http import HTTPStatus
from datetime import datetime

# Error Handling Imports
from .errors import BadRequest
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError


@app.route('/')
def hello_world():
    return 'Hello, World!'


# USER ROUTES
@app.route('/users', methods=['POST'])
def add_user():
    try:
        data = UserSchema().load(request.get_json().get('user'))
        new_user = User(**data)
    except ValidationError as e:
        raise BadRequest(e.messages)

    try:
        db.session.add(new_user)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise BadRequest('Email or username is already taken.')
    else:
        db.session.commit() 
        body = {'user' : UserSchema().dump(new_user)}
        return jsonify(body), HTTPStatus.CREATED


@app.route('/users', methods=['GET'])
def get_all_users():
    all_users = User.query.all()
    body = {'users': UserSchema().dump(all_users, many=True)}
    
    return jsonify(body), HTTPStatus.OK


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    body = {'user' : UserSchema().dump(user)}

    return jsonify(body), HTTPStatus.OK


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        raise BadRequest('Resource not found.', status=HTTPStatus.NOT_FOUND)
    try:
        data = UserSchema(partial=True).load(request.get_json().get('user'))
    except ValidationError as e:
        raise BadRequest(e.messages)
    
    for attr, val in data.items():
        setattr(user, attr, val)
    
    user.updated_at = datetime.now()
    db.session.add(user)
    db.session.commit()
    
    body = {'user' : UserSchema().dump(user)}

    return jsonify(body), HTTPStatus.OK


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        User.query.filter(User.id == self.id).delete()
        db.session.commit()
    else:
        raise BadRequest('Resource not found.', status=HTTPStatus.NOT_FOUND)
    
    return '', HTTPStatus.NO_CONTENT
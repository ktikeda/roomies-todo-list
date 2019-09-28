from flask import request, jsonify
from marshmallow import ValidationError
from roomies_todo_list import app, db
from .models import User, UserSchema


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/users', methods=['POST'])
def add_user():
    try:
        new_user = UserSchema().load(request.get_json())
        db.session.add(new_user)
        db.session.commit()
        response = {'user' : UserSchema().dump(new_user)}

        return response, 201

    except ValidationError as e:
        return jsonify(e.messages), 400

@app.route('/users')
def get_all_users():
    all_users = User.query.all()
    response = {'users': UserSchema().dump(all_users, many=True)}
    
    return jsonify(response)
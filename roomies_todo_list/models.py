from datetime import datetime

from flask_login import UserMixin
from marshmallow import Schema, fields, post_load
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from roomies_todo_list import login
from roomies_todo_list import db

class BadRequest(Exception):
    """Custom exception class to be thrown when local error occurs."""
    def __init__(self, message, status=400, payload=None):
        self.message = message
        self.status = status
        self.payload = payload

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    """
    Create an Users table
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    email = db.Column(db.String(60), index=True, unique=True)
    username = db.Column(db.String(60), index=True, unique=True)
    first_name = db.Column(db.String(60), index=True)
    last_name = db.Column(db.String(60), index=True)
    password_hash = db.Column(db.String(128))
    tasks = relationship('Task', secondary='tasks_assignees')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, username, **kwargs):
        self.email = email
        self.username = username

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)

    def __repr__(self):
        return f"<User: id={self.id} username={self.username} email={self.email}>"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSchema(Schema):
    id = fields.Integer() # TODO: Ensure that we cannot upate ID via put request
    email = fields.Email(required=True, error_messages={"required": "Email is required."})
    username = fields.Str(required=True, error_messages={"required": "Username is required."})
    first_name = fields.Str()
    last_name = fields.Str()
    tasks = fields.List(fields.Nested('TaskSchema', only=('id', 'name')))
    password_hash = fields.Str(load_only=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'tasks')
        ordered = True


class Task(db.Model):

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(120), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), default=None, nullable=True)
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    assignees = relationship("User", secondary='tasks_assignees')
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, name, created_by, **kwargs):
        self.name = name
        self.created_by = created_by
        self.created_by_id = created_by.id

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)

    def __repr__(self):
        return f"<Task: id={self.id} name={self.name} created_by={self.created_by}>"


class TaskSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.Str()
    description = fields.Str()
    created_by = fields.Nested('UserSchema', only=('id', 'username', 'email'))
    completed_by = fields.Nested('UserSchema', only=('id', 'username', 'email'))
    assignees = fields.List(fields.Nested('UserSchema', only=('id', 'username', 'email')))
    due_date = fields.DateTime()
    completed_at = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    is_completed = fields.Boolean()
    

    class Meta:
        model = Task
        fields = ('id', 'name', 'description', 'created_by', 'completed_at', 'due_date', 'completed_by', 'assignees', 'is_completed')


class TaskAssignee(db.Model):

    __tablename__ = 'tasks_assignees'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # TODO: Debug unique constraint
    #__table_args__ = (UniqueConstraint('task_id', 'user_id', name='_task_user_uc'),)

    def __init__(self, task_id, user_id, **kwargs):
        self.task_id = task_id
        self.user_id = user_id

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)

    def __repr__(self):
        return f"<TaskAssignee: id={self.id} task_id={self.task_id} user_id={self.user_id}>"

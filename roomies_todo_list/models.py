from roomies_todo_list import db
from datetime import datetime
from marshmallow import Schema, fields, post_load


class User(db.Model):
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, username, **kwargs):
        self.email = email
        self.username = username

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)
        
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<User: id={self.id} username={self.username} email={self.email}>"


class UserSchema(Schema):
    id = fields.Integer()
    email = fields.Email(required=True, error_messages={"required": "Email is required."})
    username = fields.Str(required=True, error_messages={"required": "Username is required."})
    first_name = fields.Str()
    last_name = fields.Str()
    password_hash = fields.Str(load_only=True)
    created_at = fields.Date()
    updated_at = fields.Date()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')
        ordered = True

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)



class Task(db.Model):

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(120), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, name, created_by, **kwargs):
        self.name = name
        self.created_by = created_by

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)
        
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Task: id={self.id} name={self.name}>"


class TaskAssignee(db.Model):

    __tablename = 'tasks_assignees'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __init__(self, task_id, user_id, **kwargs):
        self.task_id = task_id
        self.user_id = user_id

        if kwargs is not None:
            for attr, val in kwargs.items():
                setattr(self, attr, val)
        
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<TaskAssignee: id={self.id} task_id={self.task_id} user_id={self.user_id}>"
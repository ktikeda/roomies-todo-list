# third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# local imports
from config import app_config

# db variable initialization
db = SQLAlchemy()


# def create_app(config_name):
app = Flask(__name__, instance_relative_config=True)
config_name = os.getenv('FLASK_ENV')
app.config.from_object(app_config[config_name])
app.config.from_pyfile('config.py')
db.init_app(app)

login = LoginManager(app)
login.login_view = 'login'

import roomies_todo_list.views

migrate = Migrate(app, db)

import roomies_todo_list.models
    # return app
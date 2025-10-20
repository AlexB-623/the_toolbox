import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Migrate(app, db)

login_manager.init_app(app)
login_manager.login_view = 'login'

#OAUTH#

#######

###BLUEPRINTS###
from base.users.views import users_blueprint
app.register_blueprint(users_blueprint, url_prefix='/users')

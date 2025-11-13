import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
registration_toggle = os.getenv('REGISTRATION_TOGGLE')
login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
Migrate(app, db)

login_manager.init_app(app)
login_manager.login_view = 'users.login'

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', ''). split(',')
ADMIN_EMAIL = [email.strip() for email in ADMIN_EMAIL if email.strip()]
app.config['ADMIN_EMAIL'] = ADMIN_EMAIL

#OAUTH#

#######

###BLUEPRINTS###
from base.users.views import users_blueprint
from base.gibbergen.views import gibbergen_blueprint
from base.lumberjack.views import lumberjack_blueprint
from base.the_usual_weather.views import the_usual_weather_blueprint
from base.admin.views import admin_blueprint

app.register_blueprint(users_blueprint, url_prefix='/users')
app.register_blueprint(gibbergen_blueprint, url_prefix='/gibbergen')
app.register_blueprint(lumberjack_blueprint, url_prefix='/lumberjack')
app.register_blueprint(the_usual_weather_blueprint, url_prefix='/the-usual-weather')
app.register_blueprint(admin_blueprint, url_prefix='/admin')

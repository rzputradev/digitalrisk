from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from config import config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV')
    app.config.from_object(config[env])

    migrate.init_app(app, db)
    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_email):
        return User.query.get(user_email)

    from .routes.auth import auth as auth_blueprint
    from .routes.marketing import marketing as marketing_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(marketing_blueprint)
    
    return app
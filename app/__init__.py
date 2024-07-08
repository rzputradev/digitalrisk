from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
import os
from app.config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models.user import User
    from app.models.address import Address
    from app.models.customer import Customer
    from app.models.application import Application
    from app.models.customer_application import CustomerApplication
    from app.models.application_statement import ApplicationStatement

    from .routes.auth import auth as auth_blueprint
    from .routes.marketing import marketing as marketing_blueprint
    from .routes.platform import platform as platform_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(marketing_blueprint)
    app.register_blueprint(platform_blueprint)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_user_by_id(user_id)

    return app

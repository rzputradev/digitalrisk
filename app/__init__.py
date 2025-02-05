from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

from app.config import config
from app.utils.filters import register_filters

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    config[env].init_app(app)
    
    app.debug = env == 'development'

    file_folder = app.config['FILE_FOLDER']
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["10000 per day", "1000 per hour"],
        storage_uri="memory://",
    )

    # Import and register blueprints
    from app.models.user import User
    from app.models.address import Address
    from app.models.customer import Customer
    from app.models.application import ApplicationType, Application
    from app.models.statement import Statement

    from .routes.auth import auth as auth_blueprint
    from .routes.marketing import marketing as marketing_blueprint
    from .routes.platform import platform as platform_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(marketing_blueprint)
    app.register_blueprint(platform_blueprint)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_user_by_id(user_id)
    
    register_filters(app)

    return app

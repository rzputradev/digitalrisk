import os
import logging
from dotenv import load_dotenv
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler

load_dotenv()

class UserRequestFilter(logging.Filter):
    def filter(self, record):
        return 'Message' in record.getMessage()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FILE_FOLDER = os.path.join(os.getcwd(), 'app/static/files')

    @staticmethod
    def init_app(app):
        """Default init_app does nothing."""
        pass

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'sqlite:///dev.db')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URI')

    @staticmethod
    def init_app(app):
        """Logging configuration for production."""
        log_dir = os.path.join(os.getcwd(), 'app/logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        dictConfig({
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] | %(levelname)s | %(message)s'
                },
            },
            'filters': {
                'user_request': {
                    '()': UserRequestFilter
                }
            },
            'handlers': {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': os.path.join(log_dir, 'app.log'),
                    'maxBytes': 5 * 1024 * 1024,
                    'backupCount': 5,
                    'formatter': 'default',
                    'filters': ['user_request']
                },
            },
            'root': {
                'level': 'INFO',
                'handlers': ['file', 'console']
            }
        })


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

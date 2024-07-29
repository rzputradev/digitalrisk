import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FILE_FOLDER = os.path.join(os.getcwd(), 'app/static/files')

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URI')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

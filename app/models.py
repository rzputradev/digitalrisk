import uuid
from datetime import datetime
from flask_login import UserMixin
from enum import Enum
from werkzeug.security import generate_password_hash
from app import db


class RoleEnum(Enum):
    user = 'user'
    admin = 'admin'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)  
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __init__(self, name, email, password, role=RoleEnum.user):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.role = role

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f'<User {self.email}>'

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
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False)  
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # def __init__(self, name=None, email=None, password=None, role=RoleEnum.user):
    #     self.name = name
    #     self.email = email
    #     self.password = generate_password_hash(password) if password else None
    #     self.role = role

    def __repr__(self):
        return f'<User {self.email}>'

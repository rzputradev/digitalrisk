from datetime import datetime, timezone
from flask_login import UserMixin
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    customers = db.relationship('Customer', back_populates='user', cascade="all, delete-orphan")

    def __init__(self, name, email, password, role=RoleEnum.user):
        super().__init__()
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.options(
            db.load_only(User.id, User.name, User.email, User.role)
        ).get(user_id)

    @staticmethod
    def get_user_by_email(email):
        return User.query.options(
            db.load_only(User.id, User.name, User.email, User.role)
        ).filter_by(email=email).first()

    def update_details(self, name=None, email=None, password=None, role=None):
        if name:
            self.name = name
        if email:
            self.email = email
        if password:
            self.password = generate_password_hash(password)
        if role:
            self.role = role
        db.session.commit()

    @staticmethod
    def delete_user(user_id):
        user = User.get_user_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()

    def __repr__(self):
        return f'{self.email}'

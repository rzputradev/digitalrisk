from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from flask_login import UserMixin
from enum import Enum

from app import db


class RoleEnum(Enum):
    user = 'user'
    admin = 'admin'


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    customers = db.relationship('Customer', back_populates='user')
    applications = db.relationship('Application', foreign_keys='Application.user_id', back_populates='user')
    statements = db.relationship('Statement', back_populates='user', foreign_keys='Statement.user_id')
    # updated_applications = db.relationship('Application', foreign_keys='Application.updated_by_id', back_populates='updated_by')
    # updated_statements = db.relationship('Statement', back_populates='updated_by', foreign_keys='Statement.updated_by_id')

    def __repr__(self):
        return f'{self.name}'
    

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


    def update(self, name=None, email=None, password=None, role=None):
            try:
                if name:
                    self.name = name
                if email:
                    self.email = email
                if password:
                    self.password = generate_password_hash(password)
                if role:
                    self.role = role
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Error updating user details: {e}")


    # @staticmethod
    # def delete(user_id):
    #     user = User.query.get(user_id)

    #     if not user:
    #         flash('User not found', 'user-danger')
    #         return redirect(url_for('platform.customer.index', data='user'))

    #     if user.role != RoleEnum.admin:
    #         flash('You do not have permission', 'user-warning')
    #         return redirect(url_for('platform.customer.index', data='user'))

    #     try:
    #         db.session.delete(user)
    #         db.session.commit()
    #         flash('User deleted successfully', 'user-success')

    #     except SQLAlchemyError as e:
    #         db.session.rollback()
    #         flash('Something went wrong!', 'user-danger')
    #         print(f'Failed to delete user: {str(e)}')


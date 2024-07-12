from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from flask import flash, redirect, url_for, request

from app import db
from app.models.address import Address

class IdTypeEnum(Enum):
    ktp = 'KTP'
    npwp = 'NPWP'


class CustomerTypeEnum(Enum):
    company = 'Company'
    individual = 'Individual'


class Customer(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    id_type = db.Column(db.Enum(IdTypeEnum), nullable=False)
    id_no = db.Column(db.String(100), nullable=False, unique=True)
    customer_type = db.Column(db.Enum(CustomerTypeEnum), nullable=False, default=CustomerTypeEnum.individual)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    user = db.relationship('User', back_populates='customers')
    address = db.relationship('Address', back_populates='customer', uselist=False, cascade="all, delete-orphan")
    applications = db.relationship('Application', back_populates='customer', cascade='all, delete-orphan')


    def __repr__(self):
        return f'{self.name}'


    @staticmethod
    def get_customer_by_id(customer_id):
        return Customer.query.get(customer_id)


    @staticmethod
    def get_customer_by_phone(phone_number):
        return Customer.query.filter_by(phone_number=phone_number).first()

    @staticmethod
    def update(self, **kwargs):
        if self.user_id != current_user.id:
            flash('You do not have permission', 'warning')
            return redirect(url_for('platform.customer.index', data='user'))
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'danger')
            print(f'Failed to update customer: {str(e)}')


    @staticmethod
    def delete(self):
        if self.user_id != current_user.id:
            flash('You do not have permission', 'warning')
            return redirect(url_for('platform.customer.index', data='user'))
        
        try:
            db.session.delete(self)
            db.session.commit()
            flash(f'{self.name} deleted successfully!', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'danger')
            print(f'Failed to delete customer: {str(e)}')



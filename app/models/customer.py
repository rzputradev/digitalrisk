from datetime import datetime, timezone, date
from app import db
from app.models.user import User
from app.models.address import Address
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError

class IdTypeEnum(Enum):
    KTP = 'KTP'
    Passport = 'NPWP'

class CustomerTypeEnum(Enum):
    Company = 'Company'
    Individual = 'Individual'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    id_type = db.Column(db.Enum(IdTypeEnum), nullable=False)
    id_no = db.Column(db.String(100), nullable=False)
    customer_type = db.Column(db.Enum(CustomerTypeEnum), nullable=False, default=CustomerTypeEnum.Individual)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    
    user = db.relationship('User', back_populates='customers')
    address = db.relationship('Address', back_populates='customer', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'{self.name}'

    @staticmethod
    def get_customer_by_id(customer_id):
        return Customer.query.get(customer_id)

    @staticmethod
    def get_customer_by_phone(phone_number):
        return Customer.query.filter_by(phone_number=phone_number).first()

    def update_details(self, name=None, phone_number=None, id_type=None, id_no=None):
        try:
            if name:
                self.name = name
            if phone_number:
                self.phone_number = phone_number
            if id_type:
                self.id_type = id_type
            if id_no:
                self.id_no = id_no
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating customer details: {e}")
            return False
        return True

    @staticmethod
    def delete_customer(customer_id):
        customer = Customer.get_customer_by_id(customer_id)
        if customer:
            db.session.delete(customer)
            db.session.commit()

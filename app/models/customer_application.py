from datetime import datetime, timezone
from enum import Enum

from app import db


class ApplicationStatus(Enum):
    on_process = 'On Process'
    approved = 'Approved'
    rejected = 'Rejected'


class CustomerApplication(db.Model):
    __tablename__ = 'customer_application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.on_process)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    user = db.relationship('User', foreign_keys=[user_id], back_populates='customer_applications')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], back_populates='updated_customer_applications')
    customer = db.relationship('Customer', back_populates='customer_applications')
    application = db.relationship('Application', back_populates='customer_applications')
    application_statements = db.relationship('ApplicationStatement', back_populates='customer_application')

    def __repr__(self):
        return f'{self.status}'


    @staticmethod
    def get_customer_application_by_id(customer_application_id):
        return CustomerApplication.query.get(customer_application_id)
    

    @staticmethod
    def get_all_customer_applications():
        return CustomerApplication.query.all()

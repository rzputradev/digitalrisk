from datetime import datetime, timezone
from enum import Enum
from flask_login import current_user
from flask import flash, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError

from app import db



class ApplicationStatus(Enum):
    on_process = 'On Process'
    approved = 'Approved'
    rejected = 'Rejected'


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    application_type_id = db.Column(db.Integer, db.ForeignKey('application_type.id'), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.on_process)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    user = db.relationship('User', back_populates='applications')
    # updated_by = db.relationship('User', foreign_keys=[updated_by_id], back_populates='updated_applications')
    customer = db.relationship('Customer', back_populates='applications')
    application_type = db.relationship('ApplicationType', back_populates='applications')
    statements = db.relationship('Statement', back_populates='application')

    def __repr__(self):
        return f'{self.id} - {self.status}'


    @staticmethod
    def get_customer_application_by_id(customer_application_id):
        return Application.query.get(customer_application_id)
    

    @staticmethod
    def get_all_customer_applications():
        return Application.query.all()
    

    @staticmethod
    def delete(application_id):
        application = Application.query.get(application_id)

        if not application:
            flash('Application not found', 'application-danger')
            return redirect(url_for('platform.application.index', data='user'))

        if application.user_id != current_user.id:
            flash('You do not have permission', 'application-warning')
            return redirect(url_for('platform.application.index', data='user'))

        try:
            db.session.delete(application)
            db.session.commit()
            flash('Your application deleted successfully', 'application-success')

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'application-danger')
            print(f'Failed to delete application: {str(e)}')




class ApplicationType(db.Model):
    __tablename__ = 'application_type'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    applications = db.relationship('Application', back_populates='application_type')
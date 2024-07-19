from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError

from app import db

class SentimentResult(Enum):
    positive = 'Positive'
    negative = 'Negative'
    neutral = 'Neutral'


class StatementTypeEnum(Enum): 
    online = 'Online'
    local = 'Local'


class Statement(db.Model):
    __tablename__ = 'statement'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=True)
    statement_type = db.Column(db.Enum(StatementTypeEnum), nullable=True)
    filename = db.Column(db.String(100), nullable=True)
    result = db.Column(db.String(100), nullable=True)
    sentiment = db.Column(db.Enum(SentimentResult), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='statements')
    # updated_by = db.relationship('User', foreign_keys=[updated_by_id], back_populates='updated_statements')
    application = db.relationship('Application', back_populates='statements')
    bank = db.relationship('Bank', back_populates='statements')


    def __repr__(self):
        return f'{self.id}, {self.sentiment}'


    @staticmethod
    def get_application__statement_by_id(application_statement_id):
        return Statement.query.get(application_statement_id)
    

    @staticmethod
    def get_all_application_statements():
        return Statement.query.all()




class Bank(db.Model):
    __tablename__ = 'bank'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    statements = db.relationship('Statement', back_populates='bank')

    def __repr__(self):
        return f'{self.name}'


    @staticmethod
    def get_bank_by_id(bank_id):
        return Bank.query.get(bank_id)
    

    @staticmethod
    def get_all_banks():
        return Bank.query.all()
    

    @staticmethod
    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
        return self
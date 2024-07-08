from datetime import datetime, timezone
from enum import Enum

from app import db

class SentimentResult(Enum):
    positive = 'Positive'
    negative = 'Negative'
    neutral = 'Neutral'


class Statement(db.Model):
    __tablename__ = 'statement'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    ocr_file = db.Column(db.String(100), nullable=True)
    sentiment_file = db.Column(db.String(100), nullable=True)
    sentiment = db.Column(db.Enum(SentimentResult), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='statements')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], back_populates='updated_statements')
    application = db.relationship('Application', back_populates='statements')


    def __repr__(self):
        return f'{self.id}'


    @staticmethod
    def get_application__statement_by_id(application_statement_id):
        return Statement.query.get(application_statement_id)
    

    @staticmethod
    def get_all_application_statements():
        return Statement.query.all()

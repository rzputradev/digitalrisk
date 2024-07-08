from datetime import datetime, timezone
from app import db


class ApplicationStatement(db.Model):
    __tablename__ = 'application_statement'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_application_id = db.Column(db.Integer, db.ForeignKey('customer_application.id'), nullable=False)
    ocr_file = db.Column(db.String(100), nullable=True)
    csv_file = db.Column(db.String(100), nullable=True)
    json_file = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='application_statements')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], back_populates='updated_application_statements')
    customer_application = db.relationship('CustomerApplication', back_populates='application_statements')


    def __repr__(self):
        return f'{self.id}'


    @staticmethod
    def get_application__statement_by_id(application_statement_id):
        return ApplicationStatement.query.get(application_statement_id)
    

    @staticmethod
    def get_all_application_statements():
        return ApplicationStatement.query.all()

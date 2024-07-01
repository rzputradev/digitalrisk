from datetime import datetime, timezone
from app import db

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True)
    street = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False, default='Indonesia')
    zip_code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    customer = db.relationship('Customer', back_populates='address')

    def __repr__(self):
        return f'{self.street}, {self.city}, {self.province}, {self.country}'

    @staticmethod
    def get_address_by_id(address_id):
        return Address.query.get(address_id)

    @staticmethod
    def get_address_by_customer_id(customer_id):
        return Address.query.filter_by(customer_id=customer_id).first()

    def update_details(self, street=None, city=None, province=None, country=None, zip_code=None):
        if street:
            self.street = street
        if city:
            self.city = city
        if province:
            self.province = province
        if country:
            self.country = country
        if zip_code:
            self.zip_code = zip_code
        db.session.commit()

    @staticmethod
    def delete_address(address_id):
        address = Address.get_address_by_id(address_id)
        if address:
            db.session.delete(address)
            db.session.commit()

from datetime import datetime, timezone
from app import db
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError


class ProvinceEnum(Enum):
    Aceh = 'Aceh'
    Bali = 'Bali'
    Banten = 'Banten'
    Bengkulu = 'Bengkulu'
    JawaTengah = 'Jawa Tengah' 
    KalimantanTengah = 'Kalimantan Tengah'  
    SulawesiTengah = 'Sulawesi Tengah' 
    JawaTimur = 'Jawa Timur'  
    KalimantanTimur = 'Kalimantan Timur'  
    NusaTenggaraTimur = 'Nusa Tenggara Timur'  
    Gorontalo = 'Gorontalo'
    DKIJakarta = 'DKI Jakarta'  
    Jambi = 'Jambi'
    Lampung = 'Lampung'
    Maluku = 'Maluku'
    KalimantanUtara = 'Kalimantan Utara' 
    MalukuUtara = 'Maluku Utara' 
    SulawesiUtara = 'Sulawesi Utara' 
    SumatraUtara = 'Sumatra Utara'  
    Papua = 'Papua'
    Riau = 'Riau'
    KepulauanRiau = 'Kepulauan Riau'  
    SulawesiTenggara = 'Sulawesi Tenggara'  
    KalimantanSelatan = 'Kalimantan Selatan' 
    SulawesiSelatan = 'Sulawesi Selatan'  
    SumatraSelatan = 'Sumatra Selatan' 
    JawaBarat = 'Jawa Barat'  
    KalimantanBarat = 'Kalimantan Barat'  
    NusaTenggaraBarat = 'Nusa Tenggara Barat'  
    PapuaBarat = 'Papua Barat' 
    SulawesiBarat = 'Sulawesi Barat' 
    SumatraBarat = 'Sumatra Barat' 
    Yogyakarta = 'Yogyakarta'


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True)
    street = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    province = db.Column(db.Enum(ProvinceEnum), nullable=True)
    country = db.Column(db.String(50), nullable=False, default='Indonesia')
    zip_code = db.Column(db.String(20), nullable=True)
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
        try:       
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
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating address details: {e}")
            return False
        return True

    @staticmethod
    def delete_address(address_id):
        address = Address.get_address_by_id(address_id)
        if address:
            db.session.delete(address)
            db.session.commit()

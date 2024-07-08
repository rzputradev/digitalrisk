from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from enum import Enum
from flask import flash 

from app import db


class ProvinceEnum(Enum):
    aceh = 'Aceh'
    bali = 'Bali'
    banten = 'Banten'
    bengkulu = 'Bengkulu'
    jawa_tengah = 'Jawa Tengah'
    kalimantan_tengah = 'Kalimantan Tengah'
    sulawesi_tengah = 'Sulawesi Tengah'
    jawa_timur = 'Jawa Timur'
    kalimantan_timur = 'Kalimantan Timur'
    nusa_tenggara_timur = 'Nusa Tenggara Timur'
    gorontalo = 'Gorontalo'
    dki_jakarta = 'DKI Jakarta'
    jambi = 'Jambi'
    lampung = 'Lampung'
    maluku = 'Maluku'
    kalimantan_utara = 'Kalimantan Utara'
    maluku_utara = 'Maluku Utara'
    sulawesi_utara = 'Sulawesi Utara'
    sumatra_utara = 'Sumatra Utara'
    papua = 'Papua'
    riau = 'Riau'
    kepulauan_riau = 'Kepulauan Riau'
    sulawesi_tenggara = 'Sulawesi Tenggara'
    kalimantan_selatan = 'Kalimantan Selatan'
    sulawesi_selatan = 'Sulawesi Selatan'
    sumatra_selatan = 'Sumatra Selatan'
    jawa_barat = 'Jawa Barat'
    kalimantan_barat = 'Kalimantan Barat'
    nusa_tenggara_barat = 'Nusa Tenggara Barat'
    papua_barat = 'Papua Barat'
    sulawesi_barat = 'Sulawesi Barat'
    sumatra_barat = 'Sumatra Barat'
    yogyakarta = 'Yogyakarta'



class Address(db.Model):
    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True, nullable=False)
    street = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    province = db.Column(db.Enum(ProvinceEnum), nullable=True)
    country = db.Column(db.String(50), nullable=False, default='Indonesia')
    zip_code = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    customer = db.relationship('Customer', back_populates='address')


    def __repr__(self):
        return f'{self.street}, {self.city}, {self.province}, {self.country}'


    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'preview-danger')
            print(f'Failed to update customer: {str(e)}')
       
       


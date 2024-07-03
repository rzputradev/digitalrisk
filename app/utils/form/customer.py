from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from app.models.address import ProvinceEnum
from app.models.customer import IdTypeEnum, CustomerTypeEnum


class CustomerForm(FlaskForm):
    # Customer fields
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(), 
        Regexp('^\d+$', message="Phone number must contain only numbers"),
        Length(max=20)
    ])
    id_type = SelectField('ID Type', choices=[(choice.name, choice.value) for choice in IdTypeEnum], validators=[DataRequired()])
    id_no = StringField('ID Number', validators=[
        DataRequired(), 
        Regexp('^\d+$', message="ID number must contain only numbers"),
        Length(max=100)
    ])
    customer_type = SelectField('Customer Type', choices=[(choice.name, choice.value) for choice in CustomerTypeEnum], validators=[DataRequired()])
    
    # Address fields
    street = StringField('Street', validators=[Optional(), Length(max=100)])
    city = StringField('City / Regency', validators=[Optional(), Length(max=50)])
    province = SelectField(
        'Province',
        choices=[(province.name, province.value) for province in ProvinceEnum],
        validators=[Optional()],
    )
    country = StringField('Country', default='Indonesia', validators=[DataRequired(), Length(max=50)])
    zip_code = StringField('Zip Code', validators=[
        Optional(), 
        Regexp('^\d+$', message="Zip code must contain only numbers"),
        Length(max=20)
    ])
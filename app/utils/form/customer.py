from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField, ValidationError, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange
from app.models.address import ProvinceEnum
from app.models.customer import IdTypeEnum, CustomerTypeEnum
from app.models.customer import Customer

def prev_phone_number_not_duplicate(form, field):
    prev = Customer.query.filter(Customer.id == form.id.data ).first()
    if prev.phone_number != field.data and Customer.query.filter_by(phone_number=field.data).first():
        raise ValidationError(' The Phone Number is already in use')

def prev_id_no_not_duplicate(form, field):
    prev = Customer.query.filter(Customer.id == form.id.data ).first()
    if prev.id_no != field.data and Customer.query.filter_by(id_no=field.data).first():
        raise ValidationError('The Id Number is already in use')


def id_no_not_duplicate(form, field):
    if Customer.query.filter_by(id_no=field.data).first():
        raise ValidationError('This ID Number is already in use')
    
def phone_number_not_duplicate(form, field):
    if Customer.query.filter_by(phone_number=field.data).first():
        raise ValidationError('This Phone Number is already in use')


province_choices = [('','Select Province')] + [(province.name, province.value) for province in ProvinceEnum]



class CreateCustomerForm(FlaskForm):
    # Customer fields
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    phone_number = IntegerField('Phone Number', validators=[
                              DataRequired(message="Phone Number is required."), 
                              NumberRange(min=0, message="Phone Number must be a positive number."),
                            phone_number_not_duplicate
                          ], 
                          render_kw={
                              'placeholder': 'Phone Number', 
                              'type': 'number', 
                              'min': '0',
                              'step': '1'
                          },)
    id_type = SelectField('ID Type', choices=[('', 'Select ID')] + [(choice.name, choice.value) for choice in IdTypeEnum], validators=[DataRequired()])
    id_no = IntegerField('ID Number', validators=[
                              DataRequired(message="Id Number is required."), 
                              NumberRange(min=0, message="Id must be a positive number."),
                              id_no_not_duplicate  
                          ], 
                          render_kw={
                              'placeholder': 'ID Number', 
                              'type': 'number', 
                              'min': '0',
                              'step': '1'
                          })
    customer_type = SelectField('Customer Type', choices=[('', 'Select Customer')] + [(choice.name, choice.value) for choice in CustomerTypeEnum], validators=[DataRequired()])
    
    # Address fields
    street = StringField('Street', validators=[Optional(), Length(max=100)])
    city = StringField('City / Regency', validators=[Optional(), Length(max=50)])
    province = SelectField(
        'Province',
        choices=province_choices,
        validators=[DataRequired()],
    )
    country = StringField('Country', default='Indonesia', validators=[DataRequired(), Length(max=50)])
    zip_code = StringField('Zip Code', validators=[
        Optional(), 
        Regexp('^\\d+$', message="Zip code must contain only numbers"),
        Length(max=20)
    ])
    submit = SubmitField('Create')




class UpdateCustomerForm(FlaskForm):
    id = HiddenField('Id', validators=[DataRequired()])
    name = StringField('Name', validators=[Optional(), Length(min=1, message='Name is required')])
    phone_number = StringField('Phone Number', validators=[
        Optional(), 
        Regexp('^\\d+$', message="Phone number must contain only numbers"),
        Length(min=1, message='Phone number is required'),
        prev_phone_number_not_duplicate
    ])
    id_type = SelectField('ID Type', choices=[(choice.name, choice.value) for choice in IdTypeEnum], validators=[Optional()])
    id_no = StringField('ID Number', validators=[
        Optional(), 
        Regexp('^\\d+$', message="ID number must contain only numbers"),
        Length(min=1, message='Id Number is required'),
        prev_id_no_not_duplicate
    ])
    customer_type = SelectField('Customer Type', choices=[(choice.name, choice.value) for choice in CustomerTypeEnum], validators=[Optional()])
    
    street = StringField('Street', validators=[Optional(), Length(max=100)])
    city = StringField('City / Regency', validators=[Optional(), Length(max=50)])
    province = SelectField(
        'Province',
        choices=[(province.name, province.value) for province in ProvinceEnum],
        validators=[Optional()],
    )
    country = StringField('Country', validators=[Optional(), Length(min=1, message='Country is required')])
    zip_code = StringField('Zip Code', validators=[
        Optional(), 
        Regexp('^\\d+$', message="Zip code must contain only numbers"),
        Length(max=20)
    ])
    
    submit = SubmitField('Update')

    
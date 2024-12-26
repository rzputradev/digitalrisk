from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField, ValidationError, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange
from app.models.address import ProvinceEnum
from app.models.customer import IdTypeEnum, CustomerTypeEnum
from app.models.customer import Customer


class CreateCustomerRelationForm(FlaskForm):
    def validate_single_word(form, field):
        if ' ' in field.data.strip():
            raise ValidationError("First Name must be a single word.")

    first_name = StringField(
        'First Name',
        validators=[
            DataRequired(message="First name is required."),
            Length(max=100, message="Name cannot exceed 100 characters."),
            validate_single_word
        ],
        render_kw={
            'placeholder': 'Enter your first name',
            'maxlength': '100'
        }
    )
    last_name = StringField(
        'Last Name',
        validators=[
            DataRequired(message="Last name is required."),
            Length(max=100, message="Name cannot exceed 100 characters.")
        ],
        render_kw={
            'placeholder': 'Enter your last name',
            'maxlength': '100'
        }
    )
    
    relation_type = SelectField(
        'Relation Type',
        choices=[('', 'Select Relation type'),  # Default option with an empty value
                 ('Related', 'Related'),
                 ('Buyer', 'Buyer'),
                 ('Seller', 'Seller')],
        validators=[DataRequired(message="Relation type is required.")],
        render_kw={
            'placeholder': 'Select relation type'
        }
    )
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, StringField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange
from app.models.application import ApplicationType, ApplicationStatusEnum

class CreateApplicationForm(FlaskForm):
    customer_id = HiddenField('Customer ID', validators=[DataRequired()])
    application_type_id = SelectField('Type', validators=[DataRequired()])
    
    amount = StringField('Amount (IDR)', 
                         validators=[
                             DataRequired(message="Amount is required."), 
                             Length(max=25, message="Amount cannot exceed 25 characters.")
                         ], 
                         render_kw={
                             'placeholder': 'Amount in IDR', 
                             'maxlength': '25'
                         })
    
    duration = StringField('Duration (months)', 
                           validators=[
                               DataRequired(message="Duration is required."), 
                               Length(max=25, message="Duration cannot exceed 25 characters.")
                           ], 
                           render_kw={
                               'placeholder': 'Duration in months', 
                               'maxlength': '25'
                           })
    
    def __init__(self, *args, **kwargs):
        super(CreateApplicationForm, self).__init__(*args, **kwargs)
        self.application_type_id.choices = [('', 'Select Application')] + [(type.id, type.name) for type in ApplicationType.query.all()]

class UpdateApplicationForm(FlaskForm):
    application_type_id = SelectField('Application Type', choices=[], coerce=int)
    status = SelectField('Status', choices=[(choice.name, choice.value) for choice in ApplicationStatusEnum], validators=[Optional()])
    
    amount = StringField('Amount (IDR)', 
                         validators=[
                             DataRequired(message="Amount is required."), 
                             Length(max=25, message="Amount exceeded")
                         ], 
                         render_kw={
                             'placeholder': 'Amount in IDR', 
                             'maxlength': '25'
                         })
    
    duration = StringField('Duration (months)', 
                           validators=[
                               DataRequired(message="Duration is required."), 
                               Length(max=10, message="Duration exceeded")
                           ], 
                           render_kw={
                               'placeholder': 'Duration in months', 
                               'maxlength': '10'
                           })
    
    submit = SubmitField('Update Application')

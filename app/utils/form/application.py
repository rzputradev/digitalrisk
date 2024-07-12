from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, StringField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange
from app.models.application import ApplicationType, ApplicationStatusEnum

class CreateApplicationForm(FlaskForm):
    customer_id = HiddenField('Customer ID', validators=[DataRequired()])
    application_type_id = SelectField('Type', validators=[DataRequired()])
    amount = IntegerField('Amount (IDR)', 
                          validators=[
                              DataRequired(message="Amount is required."), 
                              NumberRange(min=0, message="Amount must be a positive number.")
                          ], 
                          render_kw={
                              'placeholder': 'Amount in IDR', 
                              'type': 'number', 
                              'min': '0',
                              'step': '1000000'
                          })
    duration = IntegerField('Duration (months)', 
                            validators=[
                                DataRequired(message="Duration is required."), 
                                NumberRange(min=1, message="Duration must be at least 1 month.")
                            ], 
                            render_kw={
                                'placeholder': 'Duration in months', 
                                'type': 'number', 
                                'min': '1'
                            })
    
    def __init__(self, *args, **kwargs):
        super(CreateApplicationForm, self).__init__(*args, **kwargs)
        self.application_type_id.choices = [('', 'Select Application')]+ [(type.id, type.name) for type in ApplicationType.query.all()]
        


class UpdateApplicationForm(FlaskForm):
    application_type_id = SelectField('Application Type', choices=[], coerce=int)
    status = SelectField('Status', choices=[(choice.name, choice.value) for choice in ApplicationStatusEnum], validators=[Optional()])
    amount = IntegerField('Amount (IDR)', 
                          validators=[
                              DataRequired(message="Amount is required."), 
                              NumberRange(min=0, message="Amount must be a positive number.")
                          ], 
                          render_kw={
                              'placeholder': 'Amount in IDR', 
                              'type': 'number', 
                              'min': '0',
                              'step': '1000000'
                          })
    duration = IntegerField('Duration (months)', 
                            validators=[
                                DataRequired(message="Duration is required."), 
                                NumberRange(min=1, message="Duration must be at least 1 months.")
                            ], 
                            render_kw={
                                'placeholder': 'Duration in months', 
                                'type': 'number', 
                                'min': '1'
                            })
    submit = SubmitField('Update Application')
    
    # def __init__(self, *args, **kwargs):
    #     super(UpdateApplicationForm, self).__init__(*args, **kwargs)
    #     self.application_type.choices = [(type.id, type.name) for type in ApplicationType.query.all()]




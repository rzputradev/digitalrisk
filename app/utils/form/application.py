from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired
from app.models.application import ApplicationType

class ApplicationForm(FlaskForm):
    customer_id = HiddenField('Customer ID', validators=[DataRequired()])
    application_type_id = SelectField('Application Type', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.application_type_id.choices = [(type.id, type.name) for type in ApplicationType.query.all()]

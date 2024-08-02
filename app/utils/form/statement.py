from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, FileField, IntegerRangeField, StringField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Optional, ValidationError
from app.models.statement import Bank
from flask_wtf.file import FileAllowed, FileRequired, FileSize


class CreateStatementForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    application_id = HiddenField('Application ID', validators=[DataRequired()])
    bank_id = SelectField('Bank', validators=[DataRequired()])
    filename = FileField('Filename', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'xls', 'xlsx', 'csv'], 'PDF, image, Excel, and CSV files only!'),
        FileSize(max_size=20 * 1024 * 1024, message='File size must be less than 20 MB!')
    ])
    submit = SubmitField('Run')

    def __init__(self, *args, **kwargs):
        super(CreateStatementForm, self).__init__(*args, **kwargs)
        self.bank_id.choices = [('', 'Select Bank')] + [(type.id, type.name) for type in Bank.query.all()]



class ParameterStatementForm(FlaskForm):
    statement_id = HiddenField('Statement ID', validators=[DataRequired()])
    detect_rotation = SelectField('Detect Rotation', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    implicit_rows= SelectField('Implicit Rows', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    borderless_tables= SelectField('Borderless Tables', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    min_confidence = IntegerRangeField('Min Confidence', default=80, validators=[DataRequired()], render_kw={'min': 0, 'max': 100})
    submit = SubmitField('Run')



def validate_currency_field(form, field):
    """
    Custom validator to ensure the field value is a valid integer and greater than 0.
    """
    try:
        value = int(field.data.replace(".", "").replace(",", ""))
        if value < 1:
            raise ValidationError("Value must be greater than 0.")
    except ValueError:
        raise ValidationError("Invalid currency format.")

class EditTransactionForm(FlaskForm):
    statement_id = StringField('ID', validators=[DataRequired()])
    datetime = DateTimeField('Date & Time', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    valuedate = DateTimeField('Value Date', format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    description = StringField('Description', validators=[DataRequired()])
    reference = StringField('Reference')
    debit = StringField('Debit', validators=[DataRequired(), validate_currency_field])
    credit = StringField('Credit', validators=[DataRequired(), validate_currency_field])
    balance = StringField('Balance', validators=[DataRequired(), validate_currency_field])
    submit = SubmitField('Save')
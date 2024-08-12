from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, FileField, IntegerRangeField, StringField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Optional, ValidationError, Length, NumberRange
from app.models.statement import Bank
from flask_wtf.file import FileAllowed, FileRequired, FileSize


class CreateStatementForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    application_id = HiddenField('Application ID', validators=[DataRequired()])
    # bank_id = SelectField('Bank', validators=[DataRequired()])
    name = StringField('Statement', validators=[DataRequired(), Length(min=1, max=100)], render_kw={'placeholder': 'Statement name'})
    filename = FileField('Filename', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'xls', 'xlsx', 'csv'], 'PDF, image, Excel, and CSV files only!'),
        FileSize(max_size=20 * 1024 * 1024, message='File size must be less than 20 MB!')
    ])
    submit = SubmitField('Submit')

    # def __init__(self, *args, **kwargs):
    #     super(CreateStatementForm, self).__init__(*args, **kwargs)
    #     self.bank_id.choices = [('', 'Select Bank')] + [(type.id, type.name) for type in Bank.query.all()]


class UpdateStatementForm(FlaskForm):
    statement_id = HiddenField('Statement ID', validators=[DataRequired()])
    name = StringField('Statement', validators=[DataRequired(), Length(min=1, max=100)])
    filename = FileField('Filename', validators=[
        Optional(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'xls', 'xlsx', 'csv'], 'PDF, image, Excel, and CSV files only!'),
        FileSize(max_size=20 * 1024 * 1024, message='File size must be less than 20 MB!')
    ])
    submit = SubmitField('Submit')


class ParameterStatementForm(FlaskForm):
    statement_id = HiddenField('Statement ID', validators=[DataRequired()])
    detect_rotation = SelectField('Detect Rotation', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    implicit_rows= SelectField('Implicit Rows', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    borderless_tables= SelectField('Borderless Tables', choices=[('', 'Select'), ('true', 'True'), ('false', 'False')], validators=[DataRequired()])
    min_confidence = IntegerRangeField('Min Confidence', default=80, validators=[DataRequired()], render_kw={'min': 0, 'max': 100})
    submit = SubmitField('Submit')


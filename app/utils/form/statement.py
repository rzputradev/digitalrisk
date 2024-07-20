from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, FileField
from wtforms.validators import DataRequired
from app.models.statement import Bank
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileSize


class CreateStatementForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    application_id = HiddenField('Application ID', validators=[DataRequired()])
    # statement_type = SelectField('Statement Type', choices=[('', 'Select Type')] + [(choice.name, choice.value) for choice in StatementTypeEnum], validators=[DataRequired()])
    bank_id = SelectField('Bank', validators=[DataRequired()])
    filename = FileField('Filename', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'xls', 'xlsx', 'csv'], 'PDF, image, Excel, and CSV files only!'),
        FileSize(max_size=20 * 1024 * 1024, message='File size must be less than 10 MB!')
    ])
    submit = SubmitField('Run')

    def __init__(self, *args, **kwargs):
        super(CreateStatementForm, self).__init__(*args, **kwargs)
        self.bank_id.choices = [('', 'Select Bank')] + [(type.id, type.name) for type in Bank.query.all()]
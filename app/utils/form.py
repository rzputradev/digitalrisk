from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, Regexp
from app.models.customer import IdTypeEnum

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(message='Name is required'),
        Length(max=80, message='Name is too long')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Enter a valid email address'),
        Length(max=120, message='Email is too long')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password is too short')
    ])
    cpassword = PasswordField('Confirm Password', validators=[
        DataRequired(message='Password confirmation is required'),
        EqualTo('password', message='Password must match')
    ])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Enter a valid email address'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
    ])



class UpdateNameForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(min=2, message="Name too short")])
    submit = SubmitField('Update Name')



class UpdatePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[Optional(), Length(min=1, message="Password is required")])
    npassword = PasswordField('New Password', validators=[Optional(), Length(min=6, message="Password too short")])
    cnpassword = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('npassword', message='Passwords must match')])
    submit = SubmitField('Update Password')
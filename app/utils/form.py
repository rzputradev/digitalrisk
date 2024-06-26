from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

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
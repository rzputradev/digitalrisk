import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.utils.form.user import RegistrationForm, LoginForm

from app import db
from app.models.user import User
from app.utils.decorators import prevent_logged_in_user
from app.utils.helper import log_message



auth = Blueprint('auth', __name__, url_prefix='/auth')



@auth.route('/login', methods=['GET', 'POST'])
@prevent_logged_in_user
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.get_user_by_email(email=email)
        if user is None:
            log_message('Email does not exist!', logging.WARNING)
            flash('Email does not exist!', 'warning')
        else:
            if user.check_password(password):
                login_user(user)
                log_message(logging.INFO, 'Login successful!')
                flash('Login successful!', 'success')
                return redirect(url_for('platform.dashboard'))
            else:
                flash('Password is incorrect', 'warning')
    return render_template('pages/auth/login.html', form=form)




@auth.route('/register', methods=['GET', 'POST'])
@prevent_logged_in_user
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        email = form.email.data.strip()
        password = form.password.data
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            new_user = User(name=name, email=email, password=password)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful!', 'success')
                log_message(logging.INFO, 'Registration successful!')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('Something went wrong!', 'danger')
                print(e)
        else:
            flash('Email already taken', 'warning')

    return render_template('pages/auth/register.html', form=form)




@login_required
@auth.route('/logout')
def logout():
    log_message(logging.info, f'User {current_user.id} logout successful!')
    logout_user()
    return redirect(url_for('marketing.homepage'))
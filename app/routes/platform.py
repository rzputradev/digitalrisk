from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.utils.form.user import UpdateNameForm, UpdatePasswordForm
from app.utils.form.customer import CreateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.routes.customer import customer as customer_blueprint
from app.routes.application import application as application_blueprint
from app.routes.statement import statement as statement_blueprint
from app.utils.helper import log_message


platform = Blueprint('platform', __name__, url_prefix='/dashboard')
platform.register_blueprint(customer_blueprint)
platform.register_blueprint(application_blueprint)
platform.register_blueprint(statement_blueprint)


@platform.route('/')
@login_required
def dashboard():
    log_message(logging.INFO, f'User {current_user.id} viewing dashboard')
    return render_template('pages/platform/dashboard.html', user=current_user)



@platform.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    name_form = UpdateNameForm(prefix='name')
    password_form = UpdatePasswordForm(prefix='password')

    if name_form.validate_on_submit() and 'name-submit' in request.form:
        try:
            name = name_form.name.data.strip()
            current_user.update(name=name)
            log_message(logging.INFO, f'User {current_user.id} updated name to {name}')
            flash('Name updated successfully!', 'success')
            return redirect(url_for('platform.settings'))
        except SQLAlchemyError as e:
            log_message(logging.ERROR, e)
            flash('Something went wrong!', 'danger')
    else:
        for field, errors in name_form.errors.items():
            for error in errors:
                flash(f'Error in the {getattr(name_form, field).label.text} field - {error}', 'danger')
        log_message(logging.ERROR, f'Form validation errors for user {current_user.id} - Invalid fields: {list(name_form.errors.keys())}')

    if password_form.validate_on_submit() and 'password-submit' in request.form:
        try:
            if current_user.check_password(password_form.password.data):
                current_user.update(password=password_form.npassword.data)
                flash('Password changed successfully!', 'success')
                log_message(logging.INFO, f'User {current_user.id} changed password')
                return redirect(url_for('platform.settings'))
            else:
                flash('Invalid password!', 'danger')
        except SQLAlchemyError as e:
            log_message(logging.ERROR, e)
            flash('Something went wrong!', 'danger')
    else:
        for field, errors in password_form.errors.items():
            for error in errors:
                flash(f'Error in the {getattr(password_form, field).label.text} field - {error}', 'danger')
        log_message(logging.ERROR, f'Form validation errors for user {current_user.id} - Invalid fields: {list(password_form.errors.keys())}')

    name_form.name.data = current_user.name

    log_message(logging.INFO, f'User {current_user.id} viewing settings')
    return render_template('pages/platform/settings.html', user=current_user, name_form=name_form, password_form=password_form)



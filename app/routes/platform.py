from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app.utils.form.user import UpdateNameForm, UpdatePasswordForm
from app.utils.form.customer import CreateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.routes.customer import customer as customer_blueprint
from app.routes.application import application as application_blueprint


platform = Blueprint('platform', __name__, url_prefix='/dashboard')
platform.register_blueprint(customer_blueprint)
platform.register_blueprint(application_blueprint)


@platform.route('/')
@login_required
def dashboard():
    return render_template('pages/platform/dashboard.html', user=current_user)



@platform.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    name_form = UpdateNameForm(prefix='name')
    password_form = UpdatePasswordForm(prefix='password')

    if name_form.validate_on_submit() and 'name-submit' in request.form:
        new_name = name_form.name.data.strip()
        current_user.update(name=new_name)
        flash('Name updated successfully!', 'success')
        return redirect(url_for('platform.settings'))
    else:
        if name_form.errors:
            flash(name_form.errors, 'danger')

    if password_form.validate_on_submit() and 'password-submit' in request.form:
        user = User.get_user_by_id(current_user.id)
        if current_user.check_password(password_form.password.data):
            user.update(password=password_form.npassword.data)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('platform.settings'))
        else:
            flash('Invalid password!', 'danger')
    else:
        if password_form.errors:
            flash(password_form.errors, 'danger')

    name_form.name.data = current_user.name
    return render_template('pages/platform/settings.html', user=current_user, name_form=name_form, password_form=password_form)



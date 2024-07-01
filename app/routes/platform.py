from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.utils.form import UpdateNameForm, UpdatePasswordForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address


platform = Blueprint('platform', __name__, url_prefix='/dashboard')


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
        try:
            current_user.update_details(name=name_form.name.data)
            db.session.commit()
            flash('Name updated successfully!', 'success')
            return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong while updating your name!', 'update-name-danger')

    if password_form.validate_on_submit() and 'password-submit' in request.form:
        try:
            if current_user.check_password(password_form.password.data):
                current_user.update_details(password=password_form.npassword.data)
                db.session.commit()
                flash('Password changed successfully!', 'password-success')
            else:
                flash('Incorrect current password!', 'warning')
            return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong while changing your password!', 'password-danger')

    name_form.name.data = current_user.name
    return render_template('pages/platform/settings.html', user=current_user, name_form=name_form, password_form=password_form)



@platform.route('/create-customer', methods=['GET', 'POST'])
def createCustomer():
    if request.method == "POST":
        pass

    return render_template('pages/platform/create-customer.html', user=current_user)



@platform.route('/my-customer')
def myCustomer():
    return render_template('pages/platform/my-customer.html', user=current_user)
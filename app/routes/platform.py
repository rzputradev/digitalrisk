from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.utils.form import UpdateNameForm, UpdatePasswordForm
from app import db
from app.models import User


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
            if name_form.name.data:
                current_user.name = name_form.name.data
                db.session.commit()
                flash('Name updated successfully!', 'success')
            return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong while updating your name!', 'danger')

    if password_form.validate_on_submit() and 'password-submit' in request.form:
        try:
            user = User.get_user_by_email(current_user.email)
            if user and check_password_hash(user.password, password_form.password.data):
                current_user.password = generate_password_hash(password_form.npassword.data)
                db.session.commit()
                flash('Password changed successfully!', 'success')
            else:
                flash('Incorrect current password!', 'warning')
            return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong while changing your password!', 'danger')

    name_form.name.data = current_user.name
    return render_template('pages/platform/settings.html', user=current_user, name_form=name_form, password_form=password_form)



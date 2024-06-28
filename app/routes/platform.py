from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash

from app.utils.form import SettingsForm
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
    form = SettingsForm()
    if form.validate_on_submit():
        try:
            if form.name.data:
                current_user.name = form.name.data
            password_updated = False
            if form.password.data:
                current_user.password = generate_password_hash(form.password.data)
                password_updated = True
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')

            if password_updated:
                logout_user()
                return redirect(url_for('auth.login'))
            else:
                return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong!', 'danger')
    

    form.name.data = current_user.name
    return render_template('pages/platform/settings.html', user=current_user, form=form)



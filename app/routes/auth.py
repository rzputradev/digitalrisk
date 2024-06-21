from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from app.utils.form import RegistrationForm

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Email or password is incorrect', 'denger')
    return render_template('login.html')


@login_required
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='pbkdf2', salt_length=16)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            new_user = User(name=name, email=email, password=hashed_password)
            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('main.index'))
            except Exception as e:
                print(e)
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
        else:
            flash('Email address already registered.', 'warning')

    return render_template('register.html', form=form)

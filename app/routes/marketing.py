from flask import Blueprint, render_template
from flask_login import current_user

marketing = Blueprint('marketing', __name__)


@marketing.route('/')
def homepage():
    return render_template('pages/marketing/homepage.html', user=current_user)


@marketing.route('/contact')
def contact():
    return render_template('pages/marketing/contact.html', user=current_user)


@marketing.route('/about')
def about():
    return render_template('pages/marketing/about.html', user=current_user)


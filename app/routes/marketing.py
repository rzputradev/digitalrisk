from flask import Blueprint, render_template

marketing = Blueprint('marketing', __name__)


@marketing.route('/')
def homepage():
    return render_template('pages/marketing/homepage.html')


@marketing.route('/contact')
def contact():
    return render_template('pages/marketing/contact.html')


@marketing.route('/about')
def about():
    return render_template('pages/marketing/about.html')


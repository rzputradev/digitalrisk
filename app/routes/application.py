from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from pytz import timezone

from app.utils.form.customer import CreateCustomerForm, UpdateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.models.application import Application


application = Blueprint('application', __name__, url_prefix='/application')


@application.route('/')
@login_required
def index():
   applications = Application.query.all()
   
   return render_template('pages/platform/application.html', user=current_user, applications=applications)
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
from app.utils.form.application import ApplicationForm


application = Blueprint('application', __name__, url_prefix='/application')


@application.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12
    
    query = Application.query.options(
        joinedload(Application.customer),
        joinedload(Application.user),
        joinedload(Application.application_type)
    )
    
    if data != 'all':
        query = query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.join(Application.customer).join(Application.user).filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.id_no.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%")
            )
        )
        
    pagination = query.order_by(Application.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    applications = pagination.items

    wib = timezone('Asia/Jakarta')
    for application in applications:
        attributes = ['created_at', 'updated_at']
        for attr in attributes:
            wib_time = getattr(application, attr).astimezone(wib)
            setattr(application, attr, wib_time.strftime('%B %d, %Y'))

    return render_template('pages/platform/application.html', user=current_user, applications=applications, pagination=pagination)




@application.route('/create', methods=['POST'])
@login_required
def create():
    form = ApplicationForm()
    if form.validate_on_submit():
        try:
            print(form.customer_id.data)
            print(form.application_type_id.data)
            new_application = Application(
                user_id=current_user.id,
                customer_id=form.customer_id.data,
                application_type_id=form.application_type_id.data,
                status='on_process'
            )
            db.session.add(new_application)
            db.session.commit()
            flash('Application created successfully!', 'application-success')
            return redirect(url_for('platform.application.index', data='mine'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'application-danger')
            print(f'Failed to add application: {str(e)}')





@application.route('/delete', methods=['POST'])
@login_required
def delete():
    application_id = request.form.get('application_id')  
    print(application_id)
    Application.delete(application_id)
    
    return redirect(url_for('platform.application.index', data='user'))

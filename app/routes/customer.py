import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from pytz import timezone
from math import ceil

from app.utils.form.customer import CreateCustomerForm, UpdateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.models.statement import Statement
from app.utils.form.application import CreateApplicationForm
from app.utils.form.statement import CreateStatementForm


customer = Blueprint('customer', __name__, url_prefix='/customer')


@customer.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12
    application_form = CreateApplicationForm()

    query = Customer.query

    if data != 'all':
        query = query.filter_by(user_id=current_user.id)
   
    if search:
        query = query.join(Customer.user).filter(or_(
            Customer.id_no.ilike(f"%{search}%"),
            Customer.phone_number.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%"),
            User.name.ilike(f"%{search}%"),
        ))

    pagination = query.order_by(Customer.created_at.desc(), Customer.name.asc()).paginate(page=page, per_page=per_page, error_out=False,)
    customers = pagination.items

    return render_template('pages/platform/customers.html', user=current_user, customers=customers, pagination=pagination, data='all',  application_form=application_form)



@customer.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    customer = Customer.query.get(id)
    if customer is None:
        abort(404, description='Customer not found')

    customer_form = UpdateCustomerForm(obj=customer)
    application_form = CreateApplicationForm()
    statement_form = CreateStatementForm()

    info = {
        'total_amount': sum([customer.applications[i].amount for i in range(len(customer.applications))]),
        'on_process': len([customer.applications[i] for i in range(len(customer.applications)) if customer.applications[i].status.name == 'on_process']),
        'approved': len([customer.applications[i] for i in range(len(customer.applications)) if customer.applications[i].status.name == 'approved']),
        'rejected': len([customer.applications[i] for i in range(len(customer.applications)) if customer.applications[i].status.name == 'rejected']),
        'total_application': len(customer.applications),
    }

    if request.method == 'POST':
        if customer_form.validate_on_submit():
            customer_form.populate_obj(customer)
            
            if not customer.address:
                customer.address = Address()

            customer_form.populate_obj(customer.address)
            
            db.session.commit()
            flash('Customer updated successfully!', 'success')
            return redirect(request.referrer or url_for('platform.customer.preview', id=customer.id))
        
        else:
            for field, errors in customer_form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(customer_form, field).label.text} field - {error}', 'danger')

    customer_form.id_type.data = customer.id_type.name
    customer_form.customer_type.data = customer.customer_type.name

    customer_form.street.data = customer.address.street if customer.address else None
    customer_form.city.data = customer.address.city if customer.address else None
    customer_form.province.data = customer.address.province.name if customer.address and customer.address.province else None
    customer_form.zip_code.data = customer.address.zip_code if customer.address else None
    customer_form.country.data = customer.address.country if customer.address else None

    return render_template('pages/platform/customer-preview.html', user=current_user, customer=customer, customer_form=customer_form, application_form=application_form, statement_form=statement_form, info=info)



@customer.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateCustomerForm()
    if request.method == 'POST':

        if form.validate_on_submit():    
            try:            
                new_customer = Customer(
                    user_id=current_user.id,
                    name=form.name.data,
                    phone_number=form.phone_number.data,
                    id_type=form.id_type.data,
                    id_no=form.id_no.data,
                    customer_type=form.customer_type.data
                )
                db.session.add(new_customer)
                db.session.commit()

                new_address = Address(
                    customer_id=new_customer.id,
                    street=form.street.data,
                    city=form.city.data,
                    province=form.province.data,
                    country=form.country.data,
                    zip_code=form.zip_code.data
                )
                db.session.add(new_address)
                db.session.commit()

                flash(f'{new_customer.name} added successfully!', 'success')
                preview_url = url_for('platform.customer.preview', id=new_customer.id)
                return redirect(preview_url)

            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Something went wrong!', 'danger')
                print(f'Failed to add customer: {str(e)}')

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')

    return render_template('pages/platform/customer-create.html', user=current_user, form=form)




@customer.route('/delete', methods=['POST'])
@login_required
def delete():
    customer_id = request.form.get('customer_id')
    customer = Customer.query.get(customer_id)

    if customer.user_id != current_user.id:
        flash('You do not have permission', 'warning')
        return redirect(request.referrer or url_for('platform.application.index', data='all'))

    if not customer:
        return abort(404, description='Customer not found')

    try:
        file_folder = current_app.config['FILE_FOLDER']
        for application in customer.applications:
            for statement in application.statements:
                file_paths = [
                    os.path.join(file_folder, statement.filename) if statement.filename else None,
                    os.path.join(file_folder, statement.ocr) if statement.ocr else None,
                    os.path.join(file_folder, statement.result) if statement.result else None
                ]

                for path in file_paths:
                    if path and os.path.exists(path):
                        os.remove(path)

        db.session.delete(customer)
        db.session.commit()

        flash('Customer deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the customer and associated statements', 'danger')
        print(f'Error: {e}')

    if request.referrer and '/customer/' in request.referrer:
        return redirect(url_for('platform.customer.index', data='user'))

    return redirect(request.referrer or url_for('platform.customer.index', data='user'))





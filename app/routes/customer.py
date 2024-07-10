from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from pytz import timezone
from math import ceil
from flask_sqlalchemy import pagination

from app.utils.form.customer import CreateCustomerForm, UpdateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.models.statement import Statement
from app.utils.form.application import ApplicationForm


customer = Blueprint('customer', __name__, url_prefix='/customer')



@customer.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12
    application_form = ApplicationForm()

    query = Customer.query.options(
        joinedload(Customer.user)
    )

    if data != 'all':
        query = query.filter_by(user_id=current_user.id)
   
    if search:
        query = query.join(Customer.user).filter(or_(
            User.name.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%")
        ))

    pagination = query.order_by(Customer.created_at.desc(), Customer.name.asc()).paginate(page=page, per_page=per_page, error_out=False,)
    customers = pagination.items

    wib = timezone('Asia/Jakarta')
    for customer in customers:
        attributes = ['created_at', 'updated_at']
        for attr in attributes:
            wib_time = getattr(customer, attr).astimezone(wib)
            setattr(customer, attr, wib_time.strftime('%B %d, %Y'))

    return render_template('pages/platform/customers.html', user=current_user, customers=customers, pagination=pagination, data='all',  application_form=application_form)



@customer.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateCustomerForm()
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

            flash(f'{new_customer.name} added successfully!', 'customer-success')
            preview_url = url_for('platform.customer.preview', id=new_customer.id)
            return redirect(preview_url)

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Something went wrong!', 'customer-danger')
            print(f'Failed to add customer: {str(e)}')

    return render_template('pages/platform/customer-create.html', user=current_user, form=form)



@customer.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    page = request.args.get('page', 1, type=int)
    per_page = 12
    customer = Customer.query.get_or_404(id)
    applications_sorted = sorted(customer.applications, key=lambda x: x.created_at, reverse=True)
    total = len(applications_sorted)
    total_pages = ceil(total / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    applications_paginated = applications_sorted[start:end]
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }

    # Get all statement by customer id, order by created_at desc
    statements = Statement.query.join(Statement.application).filter_by(customer_id=id).order_by(Statement.created_at.desc()).all()


    customer_form = UpdateCustomerForm(obj=customer)
    application_form = ApplicationForm()
    if customer.address:
        customer_form = UpdateCustomerForm(obj=customer.address)

    if customer_form.validate_on_submit():
        preview_url = url_for('platform.customer.preview', id=customer.id)
        if customer.user_id != current_user.id:
            flash('You are not authorized!', 'preview-denger')
            return redirect(url_for('platform.customer.index', data='all'))
        
        customer.update(
            name=customer_form.name.data,
            phone_number=customer_form.phone_number.data,
            id_type=customer_form.id_type.data,
            id_no=customer_form.id_no.data,
            customer_type=customer_form.customer_type.data
        )

        if not customer.address:
            customer.address = Address()

        customer.address.update(
            street=customer_form.street.data,
            city=customer_form.city.data,
            province=customer_form.province.data,
            country=customer_form.country.data,
            zip_code=customer_form.zip_code.data
        )

        flash('Customer updated successfully!', 'preview-success')
        preview_url = url_for('platform.customer.preview', id=customer.id)
        return redirect(preview_url)

    wib = timezone('Asia/Jakarta')
    attributes = ['created_at', 'updated_at']
    for attr in attributes:
        wib_time = getattr(customer, attr).astimezone(wib)
        setattr(customer, attr, wib_time.strftime('%Y/%m/%d %H:%M:%S'))

    customer_form.id.data = customer.id
    customer_form.name.data = customer.name
    customer_form.phone_number.data = customer.phone_number
    customer_form.id_type.data = customer.id_type.name
    customer_form.id_no.data = customer.id_no
    customer_form.customer_type.data = customer.customer_type.name
    
    customer_form.street.data = customer.address.street
    customer_form.city.data = customer.address.city
    customer_form.province.data = customer.address.province.name
    customer_form.zip_code.data = customer.address.zip_code
    customer_form.country.data = customer.address.country

    return render_template('pages/platform/customer-preview.html', user=current_user, customer=customer, customer_form=customer_form, application_form=application_form, pagination=pagination, applications=applications_paginated, sentiments=statements)



@customer.route('/delete', methods=['POST'])
@login_required
def delete():
    customer_id = request.form.get('customer_id')  
    Customer.delete(customer_id)
    
    return redirect(url_for('platform.customer.index', data='user'))




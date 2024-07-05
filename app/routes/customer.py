from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
import pytz

from app.utils.form.customer import CreateCustomerForm, UpdateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address


customer = Blueprint('customer', __name__, url_prefix='/customer')


# def handle_integrity_error(e):
#     error_message = str(e.orig)
    
#     if 'Duplicate entry' in error_message:
#         field = error_message.split("for key '")[1].split("'")[0]
#         return f'Duplicate: {field} already exists.'
#     else:
#         return 'An error occurred while processing your request. Please try again later.'


@customer.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12

    if data == 'all':
        query = Customer.query.options(joinedload(Customer.user))
    else:
        query = Customer.query.filter_by(user_id=current_user.id).options(joinedload(Customer.user))

    if search:
        query = query.join(Customer.user).filter(or_(
            User.name.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%")
        ))

    pagination = query.order_by(Customer.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    wib = pytz.timezone('Asia/Jakarta')
    for customer in customers:
        # customer.created_at = customer.created_at.astimezone(wib)
        created_at_local = customer.created_at.astimezone(wib)
        formatted_created_at = created_at_local.strftime('%Y/%m/%d')
        customer.created_at = formatted_created_at

    return render_template('pages/platform/customers.html', user=current_user, customers=customers, pagination=pagination, data='all')



@customer.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateCustomerForm()
    if form.validate_on_submit():
        # if Customer.query.filter_by(phone_number=form.phone_number.data).first():
        #     flash('Warning: This Phone Number is already in use!', 'customer-warning')
        #     return redirect(url_for('platform.customer.index', data='all', form=form))
        
        # if Customer.query.filter_by(id_no=form.id_no.data).first():
        #     flash('Warning: This ID Number is already in use!', 'customer-warning')
        #     return redirect(url_for('platform.customer.index', data='all', form=form))
        
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

            flash(f'Customer {new_customer.name} added successfully!', 'customer-success')
            preview_url = url_for('platform.customer.preview', id=new_customer.id)
            return redirect(preview_url)

        # except IntegrityError as e:
        #     db.session.rollback()
        #     error_message = handle_integrity_error(e)
        #     flash(error_message, 'customer-create-error')
        #     print(f'Failed to add customer: {error_message}')

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Danger: Something went wrong!', 'customer-danger')
            print(f'Failed to add customer: {str(e)}')

    return render_template('pages/platform/customer-create.html', user=current_user, form=form)



@customer.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    
    customer = Customer.query.get_or_404(id)

    form = UpdateCustomerForm(obj=customer)
    if customer.address:
        form = UpdateCustomerForm(obj=customer.address)

    if form.validate_on_submit():
        preview_url = url_for('platform.customer.preview', id=customer.id)
        if customer.user_id != current_user.id:
            flash('You are not authorized!', 'preview-denger')
            return redirect(url_for('platform.customer.index', data='all'))
        
        # existing_phone_number = Customer.query.filter_by(phone_number=form.phone_number.data).first()
        # if existing_phone_number and existing_id_no.id_no !=:
        #     flash('Phone number already in use!', 'preview-warning')
        #     return redirect(preview_url)
        
        # existing_id_no = Customer.query.filter_by(id_no=form.id_no.data).first()
        # if existing_id_no:
        #     flash('Id number already in use!', 'preview-warning')
        #     return redirect(preview_url)
        
        try:
            customer.update_details(
                name=form.name.data,
                phone_number=form.phone_number.data,
                id_type=form.id_type.data,
                id_no=form.id_no.data,
                customer_type=form.customer_type.data
            )

            if not customer.address:
                customer.address = Address()

            customer.address.update_details(
                street=form.street.data,
                city=form.city.data,
                province=form.province.data,
                country=form.country.data,
                zip_code=form.zip_code.data
            )

            flash('Customer updated successfully!', 'preview-success')
            preview_url = url_for('platform.customer.preview', id=customer.id)
            return redirect(preview_url)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error updating customer details: {str(e)}', 'preview-danger')
    
    wib = pytz.timezone('Asia/Jakarta')
    created_wib_time = customer.created_at.astimezone(wib)
    updated_wib_time = customer.updated_at.astimezone(wib)
    customer.created_at = created_wib_time.strftime('%Y/%m/%d %H:%M:%S')
    customer.updated_at = updated_wib_time.strftime('%Y/%m/%d %H:%M:%S')

    address = Address.query.filter_by(customer_id=customer.id).first()

    owner = User.query.filter_by(id=customer.user_id).first()

    form.id.data = customer.id
    form.name.data = customer.name
    form.phone_number.data = customer.phone_number
    form.id_type.data = customer.id_type.name
    form.id_no.data = customer.id_no
    form.customer_type.data = customer.customer_type.name
    
    form.street.data = address.street
    form.city.data = address.city
    form.province.data = address.province.name
    form.zip_code.data = address.zip_code
    form.country.data = address.country

    return render_template('pages/platform/customer-preview.html', user=current_user, customer=customer, address=address, owner=owner, form=form)



@customer.route('/update', methods=['POST'])
@login_required
def update():
    pass


@customer.route('/delete', methods=['POST'])
@login_required
def delete():
    customer_id = request.form.get('customer_id')
    customer = Customer.query.get(customer_id)
    
    if not customer:
        flash('Customer not found', 'customer-danger')
        return redirect(url_for('platform.customer.index', data='user')) 
    
    if customer.user_id != current_user.id:
        flash('You do not have permission', 'customer-danger')
        return redirect(url_for('platform.customer.index', data='user'))  
    
    try:
        db.session.delete(customer)
        db.session.commit()
        flash('Your customer deleted successfully', 'customer-success')
    except Exception as e:
        db.session.rollback()
        flash('Something went wrong!', 'customer-error')
    
    return redirect(url_for('platform.customer.index',  data='user'))  




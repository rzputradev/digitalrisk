from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pytz

from app.utils.form.user import UpdateNameForm, UpdatePasswordForm
from app.utils.form.customer import CustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address


customer = Blueprint('customer', __name__, url_prefix='/customer')


def handle_integrity_error(e):
    error_message = str(e.orig)
    
    if 'Duplicate entry' in error_message:
        field = error_message.split("for key '")[1].split("'")[0]
        return f'Duplicate: {field} already exists.'
    else:
        return 'An error occurred while processing your request. Please try again later.'


@customer.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = CustomerForm()
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

            flash(f'Customer {new_customer.name} added successfully!', 'customer-create-success')
            return redirect(url_for('platform.customer.index', data='user'))

        except IntegrityError as e:
            db.session.rollback()
            error_message = handle_integrity_error(e)
            flash(error_message, 'customer-create-error')
            print(f'Failed to add customer: {error_message}')

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Something went wrong: {str(e)}', 'customer-create-error')
            print(f'Failed to add customer: {str(e)}')

    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 10

    if data == 'all':
        query = Customer.query
    else:
        query = Customer.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    wib = pytz.timezone('Asia/Jakarta')
    for customer in customers:
        customer.created_at = customer.created_at.astimezone(wib)

    return render_template('pages/platform/customers.html', user=current_user, customers=customers, pagination=pagination, form=form)







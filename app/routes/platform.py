from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app.utils.form.user import UpdateNameForm, UpdatePasswordForm
from app.utils.form.customer import CreateCustomerForm
from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.routes.customer import customer as customer_blueprint


platform = Blueprint('platform', __name__, url_prefix='/dashboard')
platform.register_blueprint(customer_blueprint)


@platform.route('/')
@login_required
def dashboard():
    return render_template('pages/platform/dashboard.html', user=current_user)



@platform.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    name_form = UpdateNameForm(prefix='name')
    password_form = UpdatePasswordForm(prefix='password')

    if name_form.validate_on_submit() and 'name-submit' in request.form:
        try:
            new_name = name_form.name.data.strip()
            current_user.update_details(name=new_name)
            flash('Name updated successfully!', 'settings-success')
            return redirect(url_for('platform.settings'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong!', 'settings-danger')

    if password_form.validate_on_submit() and 'password-submit' in request.form:
        try:
            user = User.get_user_by_id(current_user.id)
            if current_user.check_password(password_form.password.data):
                user.update_details(password=password_form.npassword.data)
                flash('Password changed successfully!', 'settings-success')
                return redirect(url_for('platform.settings'))
            else:
                flash('Incorrect current password!', 'settings-warning')
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong!', 'setting-danger')

    name_form.name.data = current_user.name
    return render_template('pages/platform/settings.html', user=current_user, name_form=name_form, password_form=password_form)




# @platform.route('/create-customer', methods=['GET', 'POST'])
# @login_required
# def createCustomer():
#     form = CreateCustomerForm()
#     if form.validate_on_submit():
#         try:
#             new_customer = Customer(
#                 user_id=current_user.id,
#                 name=form.name.data,
#                 phone_number=form.phone_number.data,
#                 id_type=form.id_type.data,
#                 id_no=form.id_no.data,
#                 customer_type=form.customer_type.data
#             )
#             db.session.add(new_customer)
#             db.session.commit()

#             new_address = Address(
#                 customer_id=new_customer.id,
#                 street=form.street.data,
#                 city=form.city.data,
#                 province=form.province.data,
#                 country=form.country.data,
#                 zip_code=form.zip_code.data
#             )
#             db.session.add(new_address)
#             db.session.commit()

#             flash('Customer added successfully!', 'customer-create-success')
#             return redirect(url_for('platform.createCustomer'))

#         except SQLAlchemyError as e:
#             db.session.rollback()
#             flash('Something went wrong!', 'customer-create-error')
#             print(f'Failed to add customer: {str(e)}')

#     return render_template('pages/platform/create-customer.html', user=current_user, form=form)





# @platform.route('/my-customer', methods=['GET', 'POST'])
# @login_required
# def myCustomer():
#     try:
#         search_query = request.form.get('search', '')
#         page = request.args.get('page', 1, type=int)
#         per_page = 10  # Number of items per page

#         if search_query:
#             pagination = db.session.query(Customer, Address).join(Address).filter(
#                 Customer.user_id == current_user.id,
#                 (Customer.name.ilike(f'%{search_query}%') | 
#                  Customer.id_no.ilike(f'%{search_query}%') | 
#                  Customer.phone_number.ilike(f'%{search_query}%'))
#             ).paginate(page=page, per_page=per_page)
#         else:
#             pagination = db.session.query(Customer, Address).join(Address).filter(
#                 Customer.user_id == current_user.id
#             ).paginate(page=page, per_page=per_page)

#         customer_address_pairs = pagination.items

#         return render_template('pages/platform/my-customer.html', 
#                                user=current_user, 
#                                customers=customer_address_pairs, 
#                                pagination=pagination, 
#                                search_query=search_query,
#                                enumerate=enumerate)
#     except SQLAlchemyError as e:
#         # Handle database errors
#         flash('An error occurred while fetching customer data.', 'error')
#         return redirect(url_for('platform.dashboard'))

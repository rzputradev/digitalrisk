import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from pytz import timezone
import logging

from app import db
from app.models.user import User
from app.models.customer import Customer, CustomerRelation
from app.models.address import Address
from app.models.application import Application, ApplicationType
from app.utils.form.application import CreateApplicationForm, UpdateApplicationForm
from app.utils.form.statement import CreateStatementForm
from app.utils.form.customer_relation import CreateCustomerRelationForm
from app.utils.helper import parse_float, log_message


customer_relation = Blueprint('customer_relation', __name__, url_prefix='/customer-relation')

@customer_relation.route('/delete', methods=['POST'])
@login_required
def delete():
    relation_id = request.form.get('relation_id')
    relation = CustomerRelation.query.get(relation_id)

    if relation is None:
        log_message(logging.WARNING, f'Customer Relation {relation_id} not found')
        return abort(404, description="Customer Relation not found")

    try:
        db.session.delete(relation)
        db.session.commit()
        log_message(logging.INFO, f'CustomerRelation {relation_id} deleted')
        flash('Customer Relation deleted successfully!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Something went wrong!', 'danger')
        print(f'Failed to delete CustomerRelation: {str(e)}')
        log_message(logging.ERROR, f'Failed to delete customer relation {relation_id}: {str(e)}')


    return redirect(request.referrer)

@customer_relation.route('/create', methods=['POST'])
@login_required
def create():
    form = CreateCustomerRelationForm()
    customer_id = request.form.get('customer_id')

    if request.method == 'POST':
        if form.validate_on_submit():
            first_name = form.first_name.data
            last_name = form.last_name.data
            name = f"{first_name} {last_name}"
            relation_type = form.relation_type.data

            new_relation = CustomerRelation(
                name=name,
                relation_type=relation_type,
                customer_id=customer_id
            )
            try:
                db.session.add(new_relation)
                db.session.commit()

                flash('Customer relation created successfully!', 'success')
                log_message(logging.INFO, f'Customer Relation  created')
                return redirect(request.referrer)
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Something went wrong!', 'danger')
                print(f'Failed to add customer relation: {str(e)}')
                log_message(logging.ERROR, f'Failed to create new customer relation: {str(e)}')
        else:
            flash('Form validation failed. Please check your inputs.', 'warning')

    return redirect(request.referrer)

@customer_relation.route('/update', methods=['POST'])
@login_required
def update():
    form = CreateCustomerRelationForm()
    customer_id = request.form.get('relation_id')

    if request.method == 'POST':
        if form.validate_on_submit():
            existing_relation = CustomerRelation.query.filter_by(id=customer_id).first()

            if existing_relation:
                existing_relation.first_name = form.first_name.data
                existing_relation.last_name = form.last_name.data
                existing_relation.name = f"{form.first_name.data} {form.last_name.data}"
                existing_relation.relation_type = form.relation_type.data

                try:
                    db.session.commit()

                    flash('Customer relation updated successfully!', 'success')
                    log_message(logging.INFO, f'Customer Relation updated for customer {customer_id}')
                    return redirect(request.referrer)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    flash('Something went wrong!', 'danger')
                    print(f'Failed to update customer relation: {str(e)}')
                    log_message(logging.ERROR, f'Failed to update customer relation: {str(e)}')
            else:
                flash('Customer relation not found.', 'danger')

        else:
            flash('Form validation failed. Please check your inputs.', 'warning')

    return redirect(request.referrer)


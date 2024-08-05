import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import json
import re

from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.application import Application
from app.models.statement import Statement
from app.utils.form.statement import CreateStatementForm, ParameterStatementForm
from app.utils.helper import generate_unique_filename, parse_currency, save_json_file, load_json_file
from datetime import datetime



statement = Blueprint('statement', __name__, url_prefix='/statement')



@statement.route('/', methods=['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12

    query = Statement.query

    if data != 'all':
        query = query.filter_by(user_id=current_user.id)

    if search:
        search_filter = or_(
            Customer.name.ilike(f"%{search}%"),
            User.name.ilike(f"%{search}%")
        )
        query = query.join(Statement.application).join(Application.customer).join(Application.user).filter(search_filter)
    
    pagination = query.options(
        joinedload(Statement.application).joinedload(Application.customer),
        joinedload(Statement.application).joinedload(Application.user)
    ).order_by(Statement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    statements = pagination.items

    return render_template('pages/platform/statement.html', user=current_user, statements=statements, pagination=pagination)




@statement.route('/<int:id>', methods=['GET'])
@login_required
def preview(id):
    statement = Statement.query.get(id)
    
    if not statement:
        abort(404, description="Statement not found")

    statement_form = CreateStatementForm()
    parameter_form = ParameterStatementForm()
    result = None

    if statement.result:
        result_json_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)
        if os.path.isfile(result_json_path):
            try:
                with open(result_json_path, 'r') as file:
                    result = json.load(file)
            except json.JSONDecodeError:
                flash('An error occurred while loading the result', 'danger')
                print('Error: An error occurred while loading the result')  

    return render_template('pages/platform/statement-preview.html', user=current_user, statement=statement, result=result, statement_form=statement_form, parameter_form=parameter_form)




@statement.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    application_id = request.args.get('application_id')
    application = Application.query.get(application_id)

    if not application:
        abort(404, description="Application not found")

    form = CreateStatementForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                file = form.filename.data
                if file:
                    secure_filename
                    unique_filename, upload_path = generate_unique_filename(secure_filename(file.filename))
                    file.save(upload_path)

                    statement = Statement(
                        user_id=form.user_id.data,
                        application_id=form.application_id.data,
                        bank_id=form.bank_id.data,
                        filename=unique_filename
                    )

                    db.session.add(statement)
                    db.session.commit()

                    flash('Statement uploaded successfully', 'success')
                    return redirect(url_for('platform.statement.preview', id=statement.id))
                else:
                    flash('No file uploaded.', 'danger')
                    return redirect(request.url)

            except SQLAlchemyError as e:
                db.session.rollback()
                flash('An error occurred while uploading the statement', 'danger')
                print(f'Error: {e}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')


    return redirect(request.referrer or url_for('platform.statement.index', data='user'))




@statement.route('/edit_transaction', methods=['POST'])
@login_required
def edit_transaction():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        return redirect(url_for('platform.statement.preview', id=statement_id))

    result_json_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)
    
    if not os.path.exists(result_json_path):
        flash('JSON file not found', 'danger')
        return redirect(url_for('platform.statement.preview', id=statement_id))
    
    result = load_json_file(result_json_path)
    if result is None:
        flash('Error loading JSON file', 'danger')
        return redirect(url_for('platform.statement.preview', id=statement_id))

    transactions = result.get('transactions', [])
    form_transactions = {
        key: value for key, value in request.form.items() if key.startswith('transactions[')
    }

    has_errors = False

    for transaction in transactions:
        transaction_id = str(transaction['id'])
        transaction_prefix = f'transactions[{transaction_id}]'

        for field in ['datetime', 'valuedate', 'description', 'reference', 'debit', 'credit', 'balance']:
            form_value = form_transactions.get(f'{transaction_prefix}[{field}]')

            if field == 'datetime' and not form_value:
                flash(f'Datetime cannot be empty for transaction ID {transaction_id}', 'danger')
                has_errors = True
                continue

            if field == 'datetime' and form_value:
                try:
                    datetime.strptime(form_value, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash(f'Invalid format for datetime for transaction ID {transaction_id}', 'danger')
                    has_errors = True
                    continue

            if field == 'valuedate':
                if form_value:
                    try:
                        datetime.strptime(form_value, '%Y-%m-%dT%H:%M') 
                    except ValueError:
                        flash(f'Invalid format for valuedate for transaction ID {transaction_id}', 'danger')
                        has_errors = True
                        continue

                    datetime_value = form_transactions.get(f'{transaction_prefix}[datetime]')
                    if datetime_value:
                        try:
                            datetime_datetime = datetime.strptime(datetime_value, '%Y-%m-%dT%H:%M')
                            datetime_valuedate = datetime.strptime(form_value, '%Y-%m-%dT%H:%M')
                            if datetime_valuedate < datetime_datetime:
                                flash(f'Value date cannot be earlier than transaction date for transaction ID {transaction_id}', 'danger')
                                has_errors = True
                                continue
                        except ValueError:
                            flash(f'Invalid date comparison for transaction ID {transaction_id}', 'danger')
                            has_errors = True
                            continue

            if field in ['description', 'reference'] and form_value:
                if len(form_value) > 150:
                    flash(f'{field.replace("_", " ").capitalize()} cannot exceed 150 characters for transaction ID {transaction_id}', 'danger')
                    has_errors = True
                    continue

            if field in ['debit', 'credit']:
                if form_value:
                    clean_value = form_value.replace(',', '')
                    if len(clean_value) > 16:
                        flash(f'{field.replace("_", " ").capitalize()} cannot exceed 16 digits for transaction ID {transaction_id}', 'danger')
                        has_errors = True
                        continue

            if field == 'balance' and form_value:
                clean_value = form_value.replace(',', '')
                if len(clean_value) > 16:
                    flash(f'Balance cannot exceed 16 digits for transaction ID {transaction_id}', 'danger')
                    has_errors = True
                    continue

            if form_value is not None:
                if field in ['debit', 'credit', 'balance']:
                    transaction[field]['value'] = parse_currency(form_value)
                else:
                    transaction[field]['value'] = form_value
            else:
                if field in ['debit', 'credit', 'balance']:
                    transaction[field]['value'] = None 

    if has_errors:
        return redirect(url_for('platform.statement.preview', id=statement_id))
    
    save_json_file(result_json_path, result)
    
    flash('Transactions updated successfully', 'success')
    return redirect(url_for('platform.statement.preview', id=statement_id))





@statement.route('/delete', methods=['POST'])
@login_required
def delete():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        abort(404, description="Statement not found")

    if statement.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this statement")
    
    try:
        file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.filename)
        if statement.filename and os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(statement)
        db.session.commit()

        flash('Statement deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the statement', 'danger')
        print(f'Error: {e}')

    return redirect(request.referrer)


import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from collections import defaultdict
from datetime import datetime
from uuid import uuid4
import json
import re

from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.application import Application
from app.models.statement import Statement
from app.models.statement import Bank
from app.utils.form.statement import CreateStatementForm, ParameterStatementForm, UpdateStatementForm
from app.utils.helper import generate_unique_filename, parse_float, save_json_file, load_json_file
from app.utils.scan.ocr import perform_ocr
from app.utils.scan.exractor import Extractor





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
                    unique_filename, upload_path = generate_unique_filename(secure_filename(file.filename))
                    file.save(upload_path)

                    statement = Statement(
                        user_id=form.user_id.data,
                        application_id=form.application_id.data,
                        name=form.name.data,
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




@statement.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    statement = Statement.query.get(id)
    
    if not statement:
        abort(404, description="Statement not found")

    statement_form = CreateStatementForm()
    parameter_form = ParameterStatementForm(bank_id=statement.bank_id)
    update_form = UpdateStatementForm()
    result = None
    transactions = None
    summary = None

    if statement.result:
        result_json_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)
        if os.path.isfile(result_json_path):
            try:
                with open(result_json_path, 'r') as file:
                    result = json.load(file)
                    transactions = result.get('transactions', [])
                    summary = result.get('summary', {})
                    if not summary:
                        summary = None
            except json.JSONDecodeError:
                flash('An error occurred while loading the result', 'danger')
                print('Error: An error occurred while loading the result') 
    
    if request.method == "POST":
        if update_form.validate_on_submit():
            try:
                file = update_form.filename.data
                if file:
                    file_folder = current_app.config['FILE_FOLDER']
                    file_paths = [
                        os.path.join(file_folder, statement.filename) if statement.filename else None,
                        os.path.join(file_folder, statement.ocr) if statement.ocr else None,
                        os.path.join(file_folder, statement.result) if statement.result else None
                    ]
                    
                    for path in file_paths:
                        if path and os.path.exists(path):
                            os.remove(path)

                    unique_filename, upload_path = generate_unique_filename(secure_filename(file.filename))
                    file.save(upload_path)
                    statement.result = None
                    statement.name = update_form.name.data
                    statement.filename = unique_filename
                else:
                    statement.name = update_form.name.data

                db.session.commit()

                flash('Statement updated successfully', 'success')
                return redirect(url_for('platform.statement.preview', id=statement.id))

            except SQLAlchemyError as e:
                db.session.rollback()
                flash('An error occurred while updating the statement', 'danger')
                print(f'Error: {e}')
        else:
            for field, errors in update_form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(update_form, field).label.text} field - {error}', 'danger')

    
    update_form.statement_id.data = statement.id
    update_form.name.data = statement.name
    # parameter_form.bank_id.data = statement.bank.name if statement.bank_id else None

    return render_template('pages/platform/statement-preview.html', user=current_user, statement=statement, transactions=transactions, summary=summary, statement_form=statement_form, parameter_form=parameter_form, update_form=update_form)




@statement.route('/view', methods=['GET'])
@login_required
def view():
    statement_id = request.args.get('statement_id')
    statement = Statement.query.get(statement_id)

    if not statement:
        abort(404, description="Statement not found")

    file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.filename)
    if not os.path.exists(file_path):
        abort(404, description="File not found")

    return render_template('components/statement/view-file.html', user=current_user, statement=statement)




@statement.route('/scan', methods=['POST'])
@login_required
def scan():
    form = ParameterStatementForm()

    if form.validate_on_submit():
        statement_id = form.statement_id.data
        full_scan = form.full_scan.data

        statement = Statement.query.get(statement_id)

        if not statement:
            flash('Statement not found', 'danger')
            return redirect(url_for('platform.statement.preview', id=statement_id))
        
        try:
            file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.filename)
            if not os.path.exists(file_path):
                flash('File not found', 'danger')
                return redirect(url_for('platform.statement.preview', id=statement_id))
            
            print(full_scan)
            
            if full_scan == '1' or not statement.ocr:
                ocr_result = perform_ocr(file_path)
                extractor = Extractor(ocr_result)
                result = extractor.extract()

                ocr_filename = statement.ocr if statement.ocr else f"{str(uuid4())}.json"
                result_filename = statement.result if statement.result else f"{str(uuid4())}.json"

                ocr_path = os.path.join(current_app.config['FILE_FOLDER'], ocr_filename)
                result_path = os.path.join(current_app.config['FILE_FOLDER'], result_filename)

                save_json_file(ocr_path, ocr_result)
                save_json_file(result_path, result)

                statement.ocr = ocr_filename
                statement.result = result_filename
            else:
                ocr_result = load_json_file(os.path.join(current_app.config['FILE_FOLDER'], statement.ocr))
                extractor = Extractor(ocr_result)
                result = extractor.extract()

                result_filename = statement.result if statement.result else f"{str(uuid4())}.json"
                result_path = os.path.join(current_app.config['FILE_FOLDER'], result_filename)

                save_json_file(result_path, result)
                statement.result = result_filename
                
            db.session.commit()

            flash('Statement scanned successfully', 'success')
            return redirect(url_for('platform.statement.preview', id=statement_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while scanning the statement', 'danger')
            print(f'Error: {e}')
            return redirect(url_for('platform.statement.preview', id=statement_id))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')
    





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

    form_transactions = {key: value for key, value in request.form.items() if key.startswith('transactions[')}

    indices = set(re.search(r'\[(\d+)\]', key).group(1) for key in form_transactions.keys())
    num_rows = len(indices)
    if num_rows < 1:
        flash('No transactions to update', 'danger')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    
    def validate_and_parse_transaction(form_data):
        transactions_dict = defaultdict(dict)
        errors = []

        for key, value in form_data.items():
            parts = key.split('[')
            if len(parts) < 3:
                continue
            index = parts[1].split(']')[0]
            field = parts[2].split(']')[0]

            confidence_key = f'transactions[{index}][{field}_confidence]'
            confidence_value = float(form_data.get(confidence_key, 0))

            faulty_key = f'transactions[{index}][{field}_faulty]'
            faulty_value = form_data.get(faulty_key, 'False') == 'True'

            if field == 'datetime':
                try:
                    if not value:
                        errors.append(f"Transaction {index}: Date and time is required.")
                    else:
                        datetime.strptime(value, '%Y-%m-%dT%H:%M')  
                    transactions_dict[index][field] = {
                        'value': value,
                        'confidence': round(confidence_value, 4),
                        'faulty': faulty_value
                    }
                except ValueError:
                    errors.append(f"Transaction {index}: Invalid date and time format.")

            elif field == 'valuedate':
                if value: 
                    try:
                        datetime.strptime(value, '%Y-%m-%dT%H:%M')  
                    except ValueError:
                        errors.append(f"Transaction {index}: Invalid value date format.")
                transactions_dict[index][field] = {
                    'value': value,
                    'confidence': round(confidence_value, 4),
                    'faulty': faulty_value
                }
            
            elif field in {'description', 'reference'}:
                if len(value) > 150:
                    errors.append(f"Transaction {index}: {field.replace('_', ' ').capitalize()} must be less than 150 characters.")
                transactions_dict[index][field] = {
                    'value': value[:150], 
                    'confidence': round(confidence_value, 4),
                    'faulty': faulty_value
                }
            
            elif field in {'debit', 'credit'}:
                if value:
                    if len(value.replace(',', '')) > 20:
                        errors.append(f"Transaction {index}: {field} must be a maximum of 20 digits.")
                    try:
                        int_value = parse_float(value)
                        transactions_dict[index][field] = {
                            'value': int_value,
                            'confidence': round(confidence_value, 4),
                            'faulty': faulty_value
                        }
                    except ValueError:
                        errors.append(f"Transaction {index}: Invalid {field} value.")
                else:
                    transactions_dict[index][field] = {
                        'value': value,
                        'confidence': round(confidence_value, 4),
                        'faulty': faulty_value
                    }
            
            elif field == 'balance':
                if not value:
                    errors.append(f"Transaction {index}: Balance is required.")
                if len(value.replace(',', '')) > 20:
                    errors.append(f"Transaction {index}: Balance must be a maximum of 20 digits.")
                try:
                    int_value = parse_float(value)
                    transactions_dict[index][field] = {
                        'value': int_value,
                        'confidence': round(confidence_value, 4),
                        'faulty': faulty_value
                    }
                except ValueError:
                    errors.append(f"Transaction {index}: Invalid balance value.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return None

        transaction_list = []
        for index, data in transactions_dict.items():
            transaction = {
                'id': int(index),
                'datetime': data.get('datetime', {}),
                'valuedate': data.get('valuedate', {}),
                'description': data.get('description', {}),
                'reference': data.get('reference', {}),
                'debit': data.get('debit', {}),
                'credit': data.get('credit', {}),
                'balance': data.get('balance', {})
            }
            transaction_list.append(transaction)

        return {'transactions': transaction_list}

    new_transactions = validate_and_parse_transaction(form_transactions)
    if new_transactions is None:
        flash('An error occurred while updating the transactions', 'danger')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))

    result['transactions'] = new_transactions['transactions']

    save_json_file(result_json_path, result)
    
    flash('Transactions updated successfully', 'success')
    return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))




@statement.route('/manual_result', methods=['POST'])
@login_required
def manual_result():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        return redirect(url_for('platform.statement.preview', id=statement_id))

    now = datetime.now()
    formatted_datetime = now.strftime("%Y-%m-%dT%H:%M")
    result = {
    "transactions": [
        {
            "id": 0,
            "datetime": {
                "value": formatted_datetime,
                "confidence": 1.0,
                "faulty": False
            },
            "valuedate": {
                "value": "",
                "confidence": 1.0,
                "faulty": False
            },
            "description": {
                "value": "",
                "confidence": 1.0,
                "faulty": False
            },
            "reference": {
                "value": "",
                "confidence": 1.0,
                "faulty": False
            },
            "debit": {
                "value": "",
                "confidence": 1.0,
                "faulty": False
            },
            "credit": {
                "value": "",
                "confidence": 1.0,
                "faulty": False
            },
            "balance": {
                "value": 0,
                "confidence": 1.0,
                "faulty": False
            }
        }]
    }

    try:
        result_filename = f"{str(uuid4())}.json"
        result_json_path = os.path.join(current_app.config['FILE_FOLDER'], result_filename)
        save_json_file(result_json_path, result)

        statement.result = result_filename
        db.session.commit()

        flash('Manual result generated successfully', 'success')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred while generating the result', 'danger')
        print(f'Error: {e}')
        return redirect(request.referrer or url_for('platform.statement.index', data='user'))




@statement.route('/reset', methods=['POST'])
@login_required
def reset():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        return redirect(url_for('platform.statement.preview', id=statement_id))

    try:
        file_folder = current_app.config['FILE_FOLDER']
        file_paths = [
            os.path.join(file_folder, statement.ocr) if statement.ocr else None,
            os.path.join(file_folder, statement.result) if statement.result else None
        ]
        
        for path in file_paths:
            if path and os.path.exists(path):
                os.remove(path)

        statement.ocr = None
        statement.result = None
        statement.bank_id = None
        db.session.commit()

        flash('Statement reset successfully', 'success')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the result', 'danger')
        print(f'Error: {e}')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))




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
        file_folder = current_app.config['FILE_FOLDER']
        file_paths = [
            os.path.join(file_folder, statement.filename) if statement.filename else None,
            os.path.join(file_folder, statement.ocr) if statement.ocr else None,
            os.path.join(file_folder, statement.result) if statement.result else None
        ]
        
        for path in file_paths:
            if path and os.path.exists(path):
                os.remove(path)
        
        db.session.delete(statement)
        db.session.commit()

        flash('Statement deleted successfully', 'success')
        return redirect(url_for('platform.statement.index', data='user'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the statement', 'danger')
        print(f'Error: {e}')

    return redirect(request.referrer)


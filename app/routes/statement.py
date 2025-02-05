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
import logging
import json
import re

from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.application import Application
from app.models.statement import Statement
from app.models.statement import Bank
from app.utils.form.statement import CreateStatementForm, ParameterStatementForm, UpdateStatementForm
from app.utils.helper import generate_unique_filename, parse_float, save_json_file, load_json_file, log_message
from app.utils.scan.ocr import perform_ocr
from app.utils.scan.exractor import Extractor
from app.utils.scan.analyze import Analyze




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
        log_message(logging.INFO, f'Searching for {search} in statements')
    
    pagination = query.options(
        joinedload(Statement.application).joinedload(Application.customer),
        joinedload(Statement.application).joinedload(Application.user)
    ).order_by(Statement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    statements = pagination.items

    log_message(logging.INFO, f'Viewing statements - Data: {data}, Search: {search}')
    return render_template('pages/platform/statement.html', user=current_user, statements=statements, pagination=pagination)




@statement.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    application_id = request.args.get('application_id')
    application = Application.query.get(application_id)

    if not application:
        log_message(logging.WARNING, f'Application {application_id} not found')
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
                    log_message(logging.INFO, f'Statement {statement.id} uploaded')
                    return redirect(url_for('platform.statement.preview', id=statement.id))
                else:
                    flash('No file uploaded.', 'danger')
                    log_message(logging.WARNING, f'No file uploaded for statement')
                    return redirect(request.url)

            except SQLAlchemyError as e:
                db.session.rollback()
                flash('An error occurred while uploading the statement', 'danger')
                print(f'Error: {e}')
                log_message(logging.ERROR, f'Failed to upload statement - {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')
            log_message(logging.ERROR, f'Form validation errors for user {current_user.id} - Invalid fields: {list(form.errors.keys())}')

    log_message(logging.INFO, f'Creating statement for application {application.id}')
    return redirect(request.referrer or url_for('platform.statement.index', data='user'))




@statement.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    statement = Statement.query.get(id)
    
    if not statement:
        log_message(logging.WARNING, f'Statement {id} not found')
        abort(404, description="Statement not found")

    statement_form = CreateStatementForm()
    parameter_form = ParameterStatementForm(bank_id=statement.bank_id)
    update_form = UpdateStatementForm()
    result = None
    transactions = []
    summary = None
    analyze = None

    if statement.result:
        result_json_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)
        if os.path.isfile(result_json_path):
            try:
                with open(result_json_path, 'r') as file:
                    result = json.load(file)
                    if result:
                        transactions = result.get('transactions', [])
                        analyze = result.get('status', {}).get('analyze', None)
                        summary = result.get('status', {}).get('summary', None)

                    log_message(logging.INFO, f'Loaded result for statement {statement.id}')
            except json.JSONDecodeError:
                flash('An error occurred while loading the result', 'danger')
                print('Error: An error occurred while loading the result') 
                log_message(logging.ERROR, f'Failed to load result for statement {statement.id}')
    
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
                log_message(logging.INFO, f'Statement {statement.id} updated')
                return redirect(url_for('platform.statement.preview', id=statement.id))

            except SQLAlchemyError as e:
                db.session.rollback()
                flash('An error occurred while updating the statement', 'danger')
                print(f'Error: {e}')
        else:
            for field, errors in update_form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(update_form, field).label.text} field - {error}', 'danger')
            log_message(logging.ERROR, f'Form validation errors for statement update - Invalid fields: {list(update_form.errors.keys())}')

    
    update_form.statement_id.data = statement.id
    update_form.name.data = statement.name
    # parameter_form.bank_id.data = statement.bank.name if statement.bank_id else None

    log_message(logging.INFO, f'Viewing statement {statement.id}')
    return render_template('pages/platform/statement-preview.html', user=current_user, statement=statement, transactions=transactions, summary=summary, analyze=analyze, statement_form=statement_form, parameter_form=parameter_form, update_form=update_form)




@statement.route('/view', methods=['GET'])
@login_required
def view():
    statement_id = request.args.get('statement_id')
    statement = Statement.query.get(statement_id)

    if not statement:
        log_message(logging.WARNING, f'Statement {statement_id} not found')
        abort(404, description="Statement not found")

    file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.filename)
    if not os.path.exists(file_path):
        log_message(logging.WARNING, f'File for statement {statement_id} not found')
        abort(404, description="File not found")

    log_message(logging.INFO, f'Viewing file for statement {statement.id}') 
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
            log_message(logging.WARNING, f'Statement {statement_id} not found')
            return redirect(url_for('platform.statement.preview', id=statement_id))
        
        try:
            file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.filename)
            if not os.path.exists(file_path):
                flash('File not found', 'danger')
                log_message(logging.WARNING, f'File for statement {statement_id} not found')
                return redirect(url_for('platform.statement.preview', id=statement_id))
            
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
                log_message(logging.INFO, f'Full scan statement')
            else:
                ocr_result = load_json_file(os.path.join(current_app.config['FILE_FOLDER'], statement.ocr))
                extractor = Extractor(ocr_result)
                result = extractor.extract()

                result_filename = statement.result if statement.result else f"{str(uuid4())}.json"
                result_path = os.path.join(current_app.config['FILE_FOLDER'], result_filename)

                save_json_file(result_path, result)
                statement.result = result_filename
                log_message(logging.INFO, f'Partial scan statement')
                
            db.session.commit()

            flash('Statement scanned successfully', 'success')
            log_message(logging.INFO, f'Statement {statement.id} scanned')
            return redirect(url_for('platform.statement.preview', id=statement_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while scanning the statement', 'danger')
            print(f'Error: {e}')
            log_message(logging.ERROR, f'Failed to scan statement {statement_id}: {str(e)}')
            return redirect(url_for('platform.statement.preview', id=statement_id))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')
        log_message(logging.ERROR, f'Form validation errors for statement scan - Invalid fields: {list(form.errors.keys())}')
    





@statement.route('/edit_transaction', methods=['POST'])
@login_required
def edit_transaction():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        log_message(logging.WARNING, f'Statement {statement_id} not found')
        return redirect(url_for('platform.statement.preview', id=statement_id))

    result_json_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)
    
    if not os.path.exists(result_json_path):
        flash('JSON file not found', 'danger')
        log_message(logging.WARNING, f'JSON file for statement {statement_id} not found')
        return redirect(url_for('platform.statement.preview', id=statement_id))
    
    result = load_json_file(result_json_path)
    if result is None:
        flash('Error loading JSON file', 'danger')
        log_message(logging.ERROR, f'Failed to load JSON file for statement {statement_id}')
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

            if field == 'datetime':
                try:
                    if not value:
                        errors.append(f"Transaction {index}: Date and time is required.")

                    transactions_dict[index][field] = {
                        'value': value,
                        'confidence': round(confidence_value, 4)
                    }
                except ValueError:
                    errors.append(f"Transaction {index}: Invalid date and time format.")

            elif field == 'valuedate':
                transactions_dict[index][field] = {
                    'value': value,
                    'confidence': round(confidence_value, 4)
                }
            
            elif field in {'description'}:
                if len(value) > 150:
                    errors.append(f"Transaction {index}: {field.replace('_', ' ').capitalize()} must be less than 150 characters.")
                transactions_dict[index][field] = {
                    'value': value[:150], 
                    'confidence': round(confidence_value, 4)
                }
            
            elif field in {'debit', 'credit'}:
                if value:
                    if len(value.replace(',', '')) > 20:
                        errors.append(f"Transaction {index}: {field} must be a maximum of 20 digits.")
                    try:
                        int_value = parse_float(value)
                        transactions_dict[index][field] = {
                            'value': int_value,
                            'confidence': round(confidence_value, 4)
                        }
                    except ValueError:
                        errors.append(f"Transaction {index}: Invalid {field} value.")
                else:
                    transactions_dict[index][field] = {
                        'value': value,
                        'confidence': round(confidence_value, 4)
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
                        'confidence': round(confidence_value, 4)
                    }
                except ValueError:
                    errors.append(f"Transaction {index}: Invalid balance value.")
            elif field == 'calculated_balance':
                transactions_dict[index][field] = {
                    'value': value,
                }
            elif field == 'balance_check':
                transactions_dict[index][field] = {
                    'value': value,
                }
            elif field == 'classification':
                transactions_dict[index][field] = {
                    'value': value,
                }

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
                'debit': data.get('debit', {}),
                'credit': data.get('credit', {}),
                'balance': data.get('balance', {}),
                'calculated_balance': data.get('calculated_balance', {}),
                'balance_check': data.get('balance_check', {}),
                'classification': data.get('classification', {}),
            }
            transaction_list.append(transaction)

        return {'transactions': transaction_list}

    new_transactions = validate_and_parse_transaction(form_transactions)
    if new_transactions is None:
        flash('An error occurred while updating the transactions', 'danger')
        log_message(logging.ERROR, f'Failed to update transactions for statement {statement_id}')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))

    if result['transactions'] == new_transactions['transactions']:
        flash('No changes made to transactions', 'warning')
        log_message(logging.INFO, f'No changes made to transactions for statement {statement_id}')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    
    result['transactions'] = new_transactions['transactions']
    save_json_file(result_json_path, result)
    flash('Transactions updated successfully', 'success')
    log_message(logging.INFO, f'Transactions updated for statement {statement_id}')
    return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))




@statement.route('/manual_result', methods=['POST'])
@login_required
def manual_result():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        log_message(logging.WARNING, f'Statement {statement_id} not found')
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
        log_message(logging.INFO, f'Manual result generated for statement {statement_id}')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred while generating the result', 'danger')
        print(f'Error: {e}')
        log_message(logging.ERROR, f'Failed to generate manual result for statement {statement_id}')
        return redirect(request.referrer or url_for('platform.statement.index', data='user'))




@statement.route('/reset', methods=['POST'])
@login_required
def reset():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        flash('Statement not found', 'danger')
        log_message(logging.WARNING, f'Statement {statement_id} not found')
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
        log_message(logging.INFO, f'Statement {statement_id} reset')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the result', 'danger')
        print(f'Error: {e}')
        log_message(logging.ERROR, f'Failed to reset statement {statement_id}')
        return redirect(request.referrer or url_for('platform.statement.preview', id=statement_id))




@statement.route('/delete', methods=['POST'])
@login_required
def delete():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)
    
    if not statement:
        log_message(logging.WARNING, f'Statement {statement_id} not found')
        abort(404, description="Statement not found")

    if statement.user_id != current_user.id:
        log_message(logging.WARNING, f'User {current_user.id} does not have permission to delete statement {statement_id}')
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
        log_message(logging.INFO, f'Statement {statement_id} deleted')
        return redirect(url_for('platform.statement.index', data='user'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the statement', 'danger')
        print(f'Error: {e}')
        log_message(logging.ERROR, f'Failed to delete statement {statement_id}')

    return redirect(request.referrer)

@statement.route('/analyze', methods=['POST'])
@login_required
def analyze():
    statement_id = request.form.get('statement_id')
    statement = Statement.query.get(statement_id)

    if not statement:
        log_message(logging.WARNING, f'Statement {statement_id} not found')
        abort(404, description="Statement not found")

    if statement.user_id != current_user.id:
        log_message(logging.WARNING, f'User {current_user.id} does not have permission to analyze statement {statement_id}')
        abort(403, description="You do not have permission to analyze this statement")
    try:
        file_path = os.path.join(current_app.config['FILE_FOLDER'], statement.result)

        if not os.path.exists(file_path):
            flash('File not found', 'danger')
            log_message(logging.WARNING, f'File for statement {statement_id} not found')
            return redirect(url_for('platform.statement.preview', id=statement_id))
        
        analyze = Analyze(file_path)
        
        try:
            analyze.process_transactions()
        except ValueError as process_error:
            flash(f'An error occurred while processing transactions: {process_error}', 'danger')
            print(f'Processing Error: {process_error}')
            log_message(logging.ERROR, f'Failed to process transactions for statement {statement_id}: {process_error}')
            return redirect(url_for('platform.statement.preview', id=statement.id))
        except Exception as e:
            flash('An unexpected error occurred while processing transactions.', 'danger')
            print(f'Unexpected Error: {e}')
            log_message(logging.ERROR, f'Unexpected error while processing transactions for statement {statement_id}: {e}')
            return redirect(url_for('platform.statement.preview', id=statement.id))

        flash('Statement analyzed successfully', 'success')
        log_message(logging.INFO, f'Statement {statement.id} analyzed')
        return redirect(url_for('platform.statement.preview', id=statement.id, tab='analyze'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error analyzing the statement', 'danger')
        print(f'Error: {e}')
        log_message(logging.ERROR, f'Failed to analyze statement {statement_id}') 


    return redirect(request.referrer)
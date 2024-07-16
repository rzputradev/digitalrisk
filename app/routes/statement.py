import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from uuid import uuid4

from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.application import Application
from app.models.statement import Statement
from app.utils.form.statement import CreateStatementForm

statement = Blueprint('statement', __name__, url_prefix='/statement')


def generate_unique_filename(original_filename):
    extension = os.path.splitext(original_filename)[1]
    unique_filename = str(uuid4()) + extension
    return unique_filename


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

    if form.validate_on_submit():
        try:
            file = form.filename.data
            if file:
                unique_filename = generate_unique_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                
                upload_path = os.path.join(upload_folder, unique_filename)

                file.save(upload_path)

                statement = Statement(
                    user_id=form.user_id.data,
                    application_id=form.application_id.data,
                    filename=unique_filename
                )

                db.session.add(statement)
                db.session.commit()

                flash('Statement uploaded successfully', 'success')
                return redirect(request.referrer)
            else:
                flash('No file uploaded.', 'danger')
                return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while uploading the statement', 'danger')
            print(f'Error: {e}')

    form.user_id.data = current_user.id
    form.application_id.data = application_id

    return render_template('pages/platform/statement-create.html', user=current_user, form=form, application=application)

 



@statement.route('/delete/<int:statement_id>', methods=['POST'])
@login_required
def delete(statement_id):
    statement = Statement.query.get_or_404(statement_id)
    
    if not statement:
        abort(404, description="Statement not found")

    if statement.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this statement")
    
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], statement.filename)
        print(file_path)
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


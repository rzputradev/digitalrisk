import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from pytz import timezone

from app import db
from app.models.user import User
from app.models.customer import Customer
from app.models.address import Address
from app.models.application import Application, ApplicationType
from app.utils.form.application import CreateApplicationForm, UpdateApplicationForm
from app.utils.form.statement import CreateStatementForm
from app.utils.helper import parse_float


application = Blueprint('application', __name__, url_prefix='/application')


@application.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    data = request.args.get('data', 'all', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 12
    
    statement_form = CreateStatementForm()
    query = Application.query
    
    if data != 'all':
        query = query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.join(Application.customer).join(Application.user).filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                ApplicationType.name.ilike(f"%{search}%"),
            )
        )
        
    pagination = query.order_by(Application.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    applications = pagination.items

    return render_template('pages/platform/application.html', user=current_user, applications=applications, pagination=pagination, statement_form=statement_form, search=search, data=data)



@application.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def preview(id):
    application = Application.query.options(joinedload(Application.statements)).get(id)
    if application is None:
        abort(404, description="Application not found")
    
    form = UpdateApplicationForm(obj=application)
    application_form = CreateApplicationForm()
    statement_form = CreateStatementForm()

    form.application_type_id.choices = [(type.id, type.name) for type in ApplicationType.query.all()]
    
    if request.method == "POST":
        if form.validate_on_submit():
            if application.user_id != current_user.id:
                flash('You do not have permission', 'warning')
                return redirect(request.referrer or url_for('platform.application.index', data='user'))
            try:
                application.application_type_id = form.application_type_id.data
                application.status = form.status.data

                amount = parse_float(form.amount.data)
                duration = parse_float(form.duration.data)

                if amount is None or duration is None:
                    flash('Invalid amount or duration format.', 'danger')
                else:
                    application.amount = amount
                    application.duration = duration
                    db.session.commit()
                    flash('Application updated successfully!', 'success')
                    return redirect(request.referrer or url_for('platform.application.index', data='user'))
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f'Failed to update application: {str(e)}')
                flash('Something went wrong!', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')

    form.status.data = application.status.name
    form.application_type_id.data = application.application_type_id

    return render_template('pages/platform/application-preview.html', user=current_user, application=application, form=form, application_form=application_form, statement_form=statement_form)





@application.route('/create', methods=['POST'])
@login_required
def create():
    form = CreateApplicationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                amount = parse_float(form.amount.data)
                duration = parse_float(form.duration.data)

                if amount is None or duration is None:
                    flash('Invalid amount or duration format.', 'danger')
                else:
                    new_application = Application(
                        user_id=current_user.id,
                        customer_id=form.customer_id.data,
                        application_type_id=form.application_type_id.data,
                        amount=amount, 
                        duration=duration, 
                        status='on_process'
                    )
                    db.session.add(new_application)
                    db.session.commit()
                    flash('Application created successfully!', 'success')
                    return redirect(url_for('platform.application.preview', id=new_application.id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Something went wrong!', 'danger')
                print(f'Failed to add application: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in the {getattr(form, field).label.text} field - {error}', 'danger')

    return redirect(request.referrer or url_for('platform.application.index', data='user'))




@application.route('/delete', methods=['POST'])
@login_required
def delete():
    application_id = request.form.get('application_id')
    application = Application.query.get(application_id)
    if application.user_id != current_user.id:
        flash('You do not have permission', 'warning')
        return redirect(request.referrer or url_for('platform.application.index', data='user'))

    if application is None:
        return abort(404, description="Application not found")

    try:
        file_folder = current_app.config['FILE_FOLDER']
        for statement in application.statements:
            file_paths = [
                os.path.join(file_folder, statement.filename) if statement.filename else None,
                os.path.join(file_folder, statement.ocr) if statement.ocr else None,
                os.path.join(file_folder, statement.result) if statement.result else None
            ]

            for path in file_paths:
                if path and os.path.exists(path):
                    os.remove(path)
        
        db.session.delete(application)
        db.session.commit()
        flash('Application deleted successfully!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Something went wrong!', 'danger')
        print(f'Failed to delete application: {str(e)}')

    if request.referrer and '/application/' in request.referrer:
        return redirect(url_for('platform.application.index', data='user'))

    return redirect(request.referrer)


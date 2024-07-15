import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from app import db
from app.models.statement import Statement
from app.models.application import Application
from app.utils.form.statement import CreateStatementForm

statement = Blueprint('statement', __name__, url_prefix='/statement')


@statement.route('/create', methods=['GET','POST'])
@login_required
def create():
   application_id = request.args.get('application_id', None)
   application = Application.query.get(application_id)

   if not application:
       abort(404, description="Application not found")

   form = CreateStatementForm()
   if form.validate_on_submit():
      try:
         file = form.ocr_raw.data
         if file:
               file.seek(0) 
               filename = secure_filename(file.filename)

               upload_folder = os.path.join(current_app.root_path, 'static/uploads')
               if not os.path.exists(upload_folder):
                  os.makedirs(upload_folder)
               upload_path = os.path.join(upload_folder, filename)

               file.save(upload_path)

               statement = Statement(
                  user_id=form.user_id.data,
                  application_id=form.application_id.data,
                  statement_type=form.statement_type.data,
                  bank_id=form.bank_id.data,
                  ocr_raw=upload_path
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
    
    if statement.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this statement")
    
    try:
        if statement.ocr_raw and os.path.exists(statement.ocr_raw):
            os.remove(statement.ocr_raw)
            
        db.session.delete(statement)
        db.session.commit()

        flash('Statement deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the statement', 'danger')
        print(f'Error: {e}')

    return redirect(request.referrer)

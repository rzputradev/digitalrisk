from datetime import datetime, timezone
from app import db


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    customer_applications = db.relationship('CustomerApplication', back_populates='application')


    def __repr__(self):
        return f'{self.name}'


    @staticmethod
    def get_application_by_id(application_id):
        return Application.query.get(application_id)
    

    @staticmethod
    def get_all_applications():
        return Application.query.all()


    # def update(self, **kwargs):
    #     try:
    #         for key, value in kwargs.items():
    #             if hasattr(self, key) and value is not None:
    #                 setattr(self, key, value)
    #         db.session.commit()

    #     except SQLAlchemyError as e:
    #         db.session.rollback()
    #         flash('Something went wrong!', 'preview-danger')
    #         print(f'Failed to update application: {str(e)}')


    # @staticmethod
    # def delete(application_id):
    #     application = Application.query.get(application_id)

    #     if current_user.role != RoleEnum.admin:
    #         flash('You do not have permission', 'application-warning')
    #         return redirect(url_for('platform.customer.index', data='user'))

    #     if not application:
    #         flash('Customer not found', 'application-danger')
    #         return redirect(url_for('platform.application.index', data='user'))
        
    #     try:
    #         db.session.delete(application)
    #         db.session.commit()
    #         flash('Your application deleted successfully', 'application-success')

    #     except SQLAlchemyError as e:
    #         db.session.rollback()
    #         flash('Something went wrong!', 'application-danger')
    #         print(f'Failed to delete application: {str(e)}')




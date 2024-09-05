from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user
from app.models.user import RoleEnum


def prevent_logged_in_user(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('platform.dashboard'))
        return view_func(*args, **kwargs)
    return decorated_function


def admin_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == RoleEnum.admin:
            return abort(403, 'You do not have permission to access this page.')
        return view_func(*args, **kwargs)
    return decorated_function
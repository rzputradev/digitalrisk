from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def prevent_logged_in_user(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('platform.dashboard'))
        return view_func(*args, **kwargs)
    return decorated_function
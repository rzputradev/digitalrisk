from flask import Blueprint, render_template
from flask_login import current_user, login_required

platform = Blueprint('platform', __name__, url_prefix='/dashboard')

@platform.route('/')
@login_required
def dashboard():
    return render_template('pages/platform/dashboard.html', user=current_user)


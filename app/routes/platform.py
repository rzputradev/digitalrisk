from flask import Blueprint, render_template
from flask_login import current_user, login_required

platform = Blueprint('platform', __name__, url_prefix='/dashboard')

@login_required
@platform.route('/')
def index():
    return render_template('pages/platform/dashboard.html', user=current_user)



from flask import current_app
from pytz import timezone

def utc_to_wib_filter(utc_datetime):
    wib_timezone = timezone('Asia/Jakarta')
    wib_datetime = utc_datetime.astimezone(wib_timezone)
    return wib_datetime.strftime('%d %B, %Y')

# Optionally register filters globally here if needed
def register_filters(app):
    app.jinja_env.filters['utc_to_wib'] = utc_to_wib_filter

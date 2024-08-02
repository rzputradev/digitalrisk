
from flask import current_app
from pytz import timezone

def utc_to_wib_filter(utc_datetime):
    wib_timezone = timezone('Asia/Jakarta')
    wib_datetime = utc_datetime.astimezone(wib_timezone)
    return wib_datetime.strftime('%d %B, %Y')


def format_wib_datetime(datetime):
    wib_timezone = timezone('Asia/Jakarta')
    wib_datetime = datetime.astimezone(wib_timezone)
    return wib_datetime.strftime('%d %B, %Y')

def format_currency(value):
    try:
        numeric_value = float(value)
        return f"{numeric_value:,.0f}".replace(",", ".") + " IDR"
    except (ValueError, TypeError):
        return value


def register_filters(app):
    app.jinja_env.filters['utc_to_wib'] = utc_to_wib_filter
    app.jinja_env.filters['format_wib_datetime'] = format_wib_datetime
    app.jinja_env.filters['format_currency'] = format_currency

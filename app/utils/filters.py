
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


def comma_separation(value, decimal_places=None, currency_symbol=None):
    try:
        numeric_value = float(value)
        
        if decimal_places is not None:
            formatted_value = f"{numeric_value:,.{decimal_places}f}"
        else:
            formatted_value = f"{numeric_value:,.0f}"
        
        if currency_symbol:
            return f"{currency_symbol} {formatted_value}"
        
        return formatted_value
    except (ValueError, TypeError):
        return value


def register_filters(app):
    app.jinja_env.filters['utc_to_wib'] = utc_to_wib_filter
    app.jinja_env.filters['format_wib_datetime'] = format_wib_datetime
    app.jinja_env.filters['comma_separation'] = comma_separation

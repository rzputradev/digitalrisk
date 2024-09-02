
from pytz import timezone
from datetime import datetime

def utc_to_wib_filter(utc_datetime):
    try:
        wib_timezone = timezone('Asia/Jakarta')
        wib_datetime = utc_datetime.astimezone(wib_timezone)
        return wib_datetime.strftime('%d %B, %Y')
    except ValueError as e:
        print(f"Error: {e}")
        return utc_datetime


def format_wib_datetime(datetime):
    try:
        wib_timezone = timezone('Asia/Jakarta')
        wib_datetime = datetime.astimezone(wib_timezone)
        return wib_datetime.strftime('%d %B, %Y %H:%M:%S')
    except ValueError as e:
        print(f"Error: {e}")
        return datetime
    

def iso_date(date_str):
    try:
        date_format = '%Y-%m-%dT%H:%M'
        datetime_obj = datetime.strptime(date_str, date_format)
        return datetime_obj.strftime("%Y-%m-%dT%H:%M")
    except ValueError as e:
        print(f"Error: {e}")
        return date_str

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
        print(f"Error: Invalid value '{value}'")
        return value


def register_filters(app):
    app.jinja_env.filters['iso_date'] = iso_date
    app.jinja_env.filters['utc_to_wib'] = utc_to_wib_filter
    app.jinja_env.filters['format_wib_datetime'] = format_wib_datetime
    app.jinja_env.filters['comma_separation'] = comma_separation

import os
import json
import re
import logging
from uuid import uuid4
from flask import current_app, request, flash
from datetime import datetime
from flask_login import current_user

def log_message(level, message, include_request_info=True):
    logger = current_app.logger
    client_ip = request.remote_addr
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'

    if include_request_info:
        request_info = f" | User ID: {user_id} | IP: {client_ip} | Method: {request.method} | Path: {request.path}"
        message = f"Message: {message}{request_info}"

    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)
    else:
        logger.info(message)




def generate_unique_filename(original_filename):
   try:
      extension = os.path.splitext(original_filename)[1]
      unique_filename = str(uuid4()) + extension
      upload_folder = current_app.config['FILE_FOLDER']
      upload_path = os.path.join(upload_folder, unique_filename)
      
      return unique_filename, upload_path
   except Exception as e:
      raise e
   

def load_json_file(filepath):
    """Load JSON data from a file."""
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        flash('An error occurred while loading the JSON file', 'danger')
        print(f'Error: {e}')
        return None


def save_json_file(filepath, data):
    """Save JSON data to a file."""
    try:
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        flash('An error occurred while saving the updated transactions', 'danger')
        print(f'Error: {e}')


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    except ValueError as e:
        flash("Conversion error", "danger")
        print(f"Error: {e}")
        return date_str
    

def parse_float(value):
    try:
        cleaned_value = re.sub(r',', '', value)
        if '.' in cleaned_value:
            return float(cleaned_value)
        else:
            return float(f"{int(cleaned_value)}.00")
    except ValueError as e:
        print(f"Error: {e}")
        return 0
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import current_app

def generate_unique_filename(original_filename):
   try:
      extension = os.path.splitext(original_filename)[1]
      unique_filename = str(uuid4()) + extension
      upload_folder = current_app.config['FILE_FOLDER']
      upload_path = os.path.join(upload_folder, unique_filename)
      
      return unique_filename, upload_path
   except Exception as e:
      raise e
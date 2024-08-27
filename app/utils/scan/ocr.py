import os
from flask import current_app, flash, abort
from uuid import uuid4

from app import db
from app.models.statement import Statement
from app.utils.helper import save_json_file


def perform_ocr(file_path):
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor

        document = DocumentFile.from_images(file_path) if file_path.lower().endswith(('.png', '.jpg', '.jpeg')) else DocumentFile.from_pdf(file_path)
        model = ocr_predictor(pretrained=True)

        result = model(document)
        json_result = result.export()

        return json_result
    except Exception as e:
        raise e



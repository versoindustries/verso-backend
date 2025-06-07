# Standard library imports
import csv
import os

# Third-party imports
from flask import abort, g, make_response, send_file, current_user
from flask_login import login_required
import json

# Local application imports
from app.models import Campaign
import app

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Utility Functions
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.after_request
def delete_file(response):
    filename = getattr(g, 'filename', None)
    if filename:
        try:
            os.remove(filename)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
    return response
        
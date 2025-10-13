# routes.py
from flask import Blueprint, jsonify, request
from src.models.extensions import db
from src.util.api import process_request, parse_word
import logging

root = logging.getLogger("root")


main_bp = Blueprint('main', __name__, url_prefix='/')

@main_bp.route("/")
def main():
    return '''
     <p>Enter word here to add to database</p>
	<form action="/get_word" method="POST">
         <input name="user_input">
         <input type="submit" value="Submit!">
    </form>
    '''

@main_bp.route("/get_word", methods=["POST"])
def get_word():
    input_word = request.form.get("user_input", "")
    try:
        process_request(input_word)
        root.info(f"Word: {input_word} added successfully")
        return f"Word: {input_word} added successfully"
    except RuntimeWarning as e:
        root.error(e)
        return str(e)
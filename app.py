#!/usr/bin/env python3
from flask import Flask, request
from logging.config import dictConfig
from src.models.extensions import db  # Import the db object
from src.util.api import process_request


app = Flask(__name__)

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s | %(module)s] %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S %Z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "worldClock.log",
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"  # Example URI
db.init_app(app) # Initialize db with the Flask app
with app.app_context(): # Create tables within the app context
    db.create_all() 
 
@app.route("/")
def main():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>Assignment</title>
    </head>
    <body style="background-color: #F0F8FF; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; margin: 0;">
    <div style="text-align: center; color: white;">
        <h1 style="color: #666;">Enter word here to add to database</h1>
        <form action="/get_word" method="POST" style="display: flex; flex-direction: column; align-items: center; margin-top: 10px;">
        <input name="user_input" placeholder="Enter something..." style="padding: 8px; margin-bottom: 5px;">
        <input type="submit" value="Submit" style="background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer;">
        </form>
    </div>
    </body>
    </html>
    '''

@app.route("/get_word", methods=["POST"])
def get_word():
    input_word = request.form.get("user_input", "")
    try:
        process_request(input_word)
        app.logger.info(f"Word: {input_word} added successfully")
        return f"Word: {input_word} added successfully"
    except RuntimeWarning as e:
        app.logger.error(e)
        return str(e)
    
if __name__ == "__main__":
    app.run(debug=True)

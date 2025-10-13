#!/usr/bin/env python3
from flask import Flask
from logging.config import dictConfig


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

@app.route("/")
def main():
    return '''
     <p>Enter word here to add to database</p>
	<form action="/get_word" method="POST">
         <input name="user_input">
         <input type="submit" value="Submit!">
    </form>
    '''

def create_app():
    from src.models.extensions import db  # Import the db object
    from src.routes.routes import main_bp  # Import the blueprint

    app.register_blueprint(main_bp)  # Register the blueprint
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"  # Example URI
    db.init_app(app) # Initialize db with the Flask app
    with app.app_context(): # Create tables within the app context
        db.create_all() 
    return app

if __name__ == "__main__":
    app = create_app()
    
    app.run(debug=True)

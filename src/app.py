#!/usr/bin/env python3
from flask import Flask
from models.extensions import db  # Import the db object
from routes import main_bp  # Import the blueprint
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

def create_app():
    app.register_blueprint(main_bp)  # Register the blueprint
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"  # Example URI
    db.init_app(app) # Initialize db with the Flask app
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context(): # Create tables within the app context
        db.create_all() 
    app.run(debug=True)

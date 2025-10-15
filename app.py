#!/usr/bin/env python3
from flask import Flask, request, render_template
from logging.config import dictConfig
from src.models.extensions import db  # Import the db object
from src.models.model import Word
from src.util.api import process_request
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
from prometheus_client import generate_latest
from flask_socketio import SocketIO, emit
from google import genai
from io import BytesIO
import base64
import os


app = Flask(__name__)

app.config.from_prefixed_env("FLASK")

API_KEY = app.config.get("API_KEY")

metrics = GunicornPrometheusMetrics(app)

async_mode = None
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=async_mode,
)

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
db.init_app(app)  # Initialize db with the Flask app
with app.app_context():  # Create tables within the app context
    db.create_all()


@app.route("/")
def main():
    return render_template("index.html", sync_mode=socketio.async_mode)


@socketio.on("search", namespace="/test")
def fetch_word_callback(data):
    try:
        input_word = data.get("wordInput")
        word = process_request(input_word)
        emit("text_response", {"data": word.to_dict()})
    except Exception as e:
        app.logger.error(msg=e)


@socketio.on("search", namespace="/test")
def fetch_image_for_word(data):
    try:
        # fetch image and emit
        input_word = data.get("wordInput")
        prompt = (
            f"As a teacher, create a picture that can teach a stundent to learn the english word {input_word} such that they will never forget"
        )

        if API_KEY:
            client = genai.Client(api_key=API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    bytes_io_object = BytesIO(part.inline_data.data)
                    binary_data = bytes_io_object.getvalue()
                    encoded_bytes = base64.b64encode(binary_data)
                    base64_image = encoded_bytes.decode('utf-8')
                    emit('image_data', 'data:image/png;base64,' + base64_image)
                    break
    except Exception as e:
        app.logger.error(e)


@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200


@app.route("/metrics")
def metrics():
    return (
        generate_latest(),
        200,
        {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"},
    )


if __name__ == "__main__":
    socketio.run(app)

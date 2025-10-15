#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Flask application tests
"""

import pytest
import tempfile
import os
from unittest.mock import patch
from flask import Flask
from flask_socketio import SocketIO
from src.models.extensions import db


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Import your main app
    from app import app, socketio
    
    # Configure for testing
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Create test client for HTTP requests"""
    return app.test_client()


@pytest.fixture(scope='function')
def socketio(app):
    """Get Socket.IO instance"""
    # Import your socketio instance
    from app import socketio
    return socketio


@pytest.fixture
def runner(app):
    """Create CLI runner for testing commands"""
    return app.test_cli_runner()


# Mock environment variables for consistent testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests"""
    with patch.dict(os.environ, {
        'API_KEY': 'test_api_key_default'
    }, clear=False):
        yield
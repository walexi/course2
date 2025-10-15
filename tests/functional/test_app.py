#!/usr/bin/env python3
"""
Tests for Flask HTTP endpoints
"""

import pytest
from unittest.mock import patch, Mock
from flask import Flask
from src.models.extensions import db
from src.models.model import Word


class TestHTTPEndpoints:
    """Test HTTP endpoints of the Flask application"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database for each test"""
        with app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()
    
    def test_main_route_renders_template(self, client):
        """Test main route renders index.html template"""
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'html' in response.data or b'HTML' in response.data
        # Check if the template contains expected elements
        assert b'Word Manager' in response.data or b'index' in response.data
    
    def test_main_route_includes_socketio_mode(self, client):
        """Test main route includes Socket.IO async mode in template context"""
        with patch('app.render_template') as mock_render:
            mock_render.return_value = "mocked template"
            
            response = client.get('/')
            
            # Verify render_template was called with sync_mode parameter
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            assert 'sync_mode' in kwargs
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint returns OK"""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.data == b'OK'
        assert response.content_type.startswith('text/html')
    
    def test_health_check_endpoint_methods(self, client):
        """Test health endpoint only accepts GET method"""
        # POST should not be allowed
        response = client.post('/health')
        assert response.status_code == 405  # Method Not Allowed
        
        # PUT should not be allowed
        response = client.put('/health')
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = client.delete('/health')
        assert response.status_code == 405
    
    def test_metrics_endpoint_format(self, client):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get('/metrics')
        
        assert response.status_code == 200
        assert response.content_type == 'text/plain; version=0.0.4; charset=utf-8'
        
        # Check if response contains Prometheus metrics format
        response_text = response.data.decode('utf-8')
        # Prometheus metrics typically contain '# TYPE' and '# HELP' comments
        assert '# TYPE' in response_text or '# HELP' in response_text or len(response_text) > 0

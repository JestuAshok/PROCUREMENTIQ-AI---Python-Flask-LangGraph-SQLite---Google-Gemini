"""
Unit and Integration Tests for Gemini AI Integration & Settings in PROCUREMENTIQ AI
"""

import os
import pytest
from app import create_app
from database.db import get_db, execute_db, query_db
from services.gemini_service import get_gemini_api_key, save_gemini_api_key, test_gemini_connection as verify_gemini_connection
from agents.requirement_parser import RequirementParserAgent
from agents.quote_analyzer import QuoteAnalyzerAgent

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_gemini_api_key_helpers(monkeypatch):
    from pathlib import Path
    monkeypatch.setattr('services.gemini_service.BASE_DIR', Path('c:/tmp_non_existent'))
    orig_key = os.environ.get('GEMINI_API_KEY')
    try:
        # Save a test key
        save_gemini_api_key("test_gemini_key_12345", user_id=1)
        assert get_gemini_api_key() == "test_gemini_key_12345"

        # Reset
        save_gemini_api_key("", user_id=1)
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        assert get_gemini_api_key() is None or get_gemini_api_key() == ""
    finally:
        if orig_key:
            save_gemini_api_key(orig_key, user_id=1)

def test_test_gemini_connection_no_key():
    success, msg = verify_gemini_connection(api_key="")
    assert success is False
    assert "No Gemini API key provided" in msg

def test_agent_fallback_and_ai_engine_metadata():
    agent = RequirementParserAgent()
    req_data = {
        "id": 999,
        "request_code": "REQ-TEST-GEMINI",
        "item_name": "Precision CNC Milling Machine",
        "category": "Heavy Machinery",
        "quantity": 2,
        "budget": 250000.0,
        "currency": "USD",
        "required_delivery_date": "2026-12-01",
        "delivery_location": "Plant Austin, TX",
        "min_warranty_months": 24,
        "payment_terms_pref": "Net 45"
    }
    result = agent.execute(req_data)
    assert result['status'] == 'Completed'
    assert 'ai_engine' in result
    assert 'ai_status' in result
    assert len(result['explanation_paragraphs']) == 3
    assert len(result['key_findings']) == 7

def test_settings_test_gemini_route(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Jahnavi'
        sess['user_email'] = 'jahnavi@procurementiq.ai'

    resp = client.post('/settings/test-gemini', data={'api_key': ''})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False
    assert "No Gemini API key" in data['message']

def test_ngrok_api_key_helpers(monkeypatch):
    from pathlib import Path
    from services.matter_service import save_ngrok_api_key, get_ngrok_api_key, test_ngrok_ai_connection
    monkeypatch.setattr('services.matter_service.BASE_DIR', Path('c:/tmp_non_existent'))
    orig_ngrok = os.environ.get('NGROK_API_KEY')
    orig_groq = os.environ.get('GROQ_API_KEY')
    try:
        save_ngrok_api_key("test_ngrok_key_999", user_id=1)
        assert get_ngrok_api_key() == "test_ngrok_key_999"

        # Reset
        save_ngrok_api_key("", user_id=1)
        if 'NGROK_API_KEY' in os.environ:
            del os.environ['NGROK_API_KEY']
        if 'GROQ_API_KEY' in os.environ:
            del os.environ['GROQ_API_KEY']

        success, msg = test_ngrok_ai_connection(api_key="")
        assert success is False
        assert "No ngrok / Groq API key" in msg
    finally:
        if orig_ngrok or orig_groq:
            save_ngrok_api_key(orig_groq or orig_ngrok, user_id=1)

def test_settings_test_ngrok_route(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Jahnavi'
        sess['user_email'] = 'jahnavi@procurementiq.ai'

    resp = client.post('/settings/test-ngrok', data={'api_key': ''})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False
    assert "No ngrok / Groq API key" in data['message']


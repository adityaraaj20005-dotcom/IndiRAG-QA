import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main
from fastapi.testclient import TestClient


def test_login_protects_library(monkeypatch):
    monkeypatch.setattr(main, 'AUTH_ENABLED', True)
    monkeypatch.setattr(main, 'TEAM_PASSWORD', 'test-password-long-enough')
    main.request_times.clear()
    client = TestClient(main.app)
    assert client.get('/api/documents').status_code == 401
    assert client.post('/api/login', json={'password': 'wrong'}).status_code == 401
    assert client.post('/api/login', json={'password': 'test-password-long-enough'}).status_code == 200
    saved_cookie = client.cookies.get('session')
    assert client.get('/api/documents').status_code == 200
    assert client.post('/api/logout').status_code == 200
    assert client.get('/api/documents').status_code == 401
    assert TestClient(main.app).get('/api/documents', headers={'Cookie': 'session=' + saved_cookie}).status_code == 401


def test_expired_session_is_rejected(monkeypatch):
    monkeypatch.setattr(main, 'AUTH_ENABLED', True)
    monkeypatch.setattr(main, 'TEAM_PASSWORD', 'test-password-long-enough')
    main.request_times.clear()
    client = TestClient(main.app)
    assert client.post('/api/login', json={'password': 'test-password-long-enough'}).status_code == 200
    for key in main.active_sessions:
        main.active_sessions[key] = 0
    assert client.get('/api/documents').status_code == 401


def test_health_and_empty_collection():
    client = TestClient(main.app)
    assert client.get('/api/health').status_code == 200
    response = client.post('/api/query', json={'question': 'test', 'collection_id': 'does-not-exist', 'generate_answer': False})
    assert response.status_code == 409


def test_rejects_untrusted_origin_and_limits_login(monkeypatch):
    monkeypatch.setattr(main, 'AUTH_ENABLED', True)
    monkeypatch.setattr(main, 'TEAM_PASSWORD', 'test-password-long-enough')
    main.request_times.clear()
    client = TestClient(main.app)
    assert client.post('/api/login', headers={'Origin': 'https://untrusted.example'}, json={'password': 'wrong'}).status_code == 403
    for _ in range(5):
        assert client.post('/api/login', json={'password': 'wrong'}).status_code == 401
    assert client.post('/api/login', json={'password': 'wrong'}).status_code == 429
    main.request_times.clear()


def test_production_origin_validation():
    assert main.secure_origin('https://demo.example')
    for origin in ('http://demo.example', 'https://*.example', 'https://demo.example/path', 'https://user:secret@demo.example'):
        assert not main.secure_origin(origin)

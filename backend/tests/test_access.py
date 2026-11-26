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
    assert client.get('/api/documents').status_code == 200
    assert client.post('/api/logout').status_code == 200
    assert client.get('/api/documents').status_code == 401


def test_health_and_empty_collection():
    client = TestClient(main.app)
    assert client.get('/api/health').status_code == 200
    response = client.post('/api/query', json={'question': 'test', 'collection_id': 'does-not-exist', 'generate_answer': False})
    assert response.status_code == 409

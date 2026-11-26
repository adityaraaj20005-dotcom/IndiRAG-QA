import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymupdf
import main
from fastapi.testclient import TestClient


def test_isolated_upload_scoping_retrieval_and_removal(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'RAW_DIR', tmp_path)
    monkeypatch.setattr(main, 'DOCUMENTS_FILE', tmp_path / 'documents.json')
    monkeypatch.setattr(main, 'PASSAGES_FILE', tmp_path / 'passages.jsonl')
    monkeypatch.setattr(main, 'documents', [])
    monkeypatch.setattr(main, 'passages', [])
    main.rebuild_index()
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), 'The annual scholarship amount is twelve thousand rupees.')
    content = pdf.tobytes()
    pdf.close()
    client = TestClient(main.app)
    upload = client.post('/api/documents/upload', files={'file': ('test.pdf', content, 'application/pdf')}, data={'collection_id': 'test-folder', 'collection_name': 'Test'})
    assert upload.status_code == 200
    doc_id = upload.json()['document']['doc_id']
    for method in ('BM25', 'TF-IDF'):
        result = client.post('/api/query', json={'question': 'scholarship amount', 'collection_id': 'test-folder', 'retrieval_method': method, 'generate_answer': False})
        assert result.status_code == 200
        assert result.json()['evidence'][0]['doc_id'] == doc_id
    assert client.post('/api/query', json={'question': 'scholarship', 'collection_id': 'other', 'generate_answer': False}).status_code == 409
    assert client.post('/api/documents/upload', files={'file': ('fake.pdf', b'not a pdf', 'application/pdf')}).status_code == 400
    assert client.delete('/api/documents/' + doc_id).status_code == 200
    assert client.get('/api/documents').json()['count'] == 0

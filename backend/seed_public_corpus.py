"""Seed approved public PDFs into an explicitly configured, empty data directory."""
import os
import urllib.request
from pathlib import Path

SOURCES = {
    'FAQ_DOHE_CSSS.pdf': 'https://www.education.gov.in/sites/upload_files/mhrd/files/upload_document/FAQs_PM_USP2526.pdf',
    'Guidelines_DOHE_CSSS.pdf': 'https://www.education.gov.in/sites/upload_files/mhrd/files/upload_document/PM_USP_CSSS_guidelines.pdf',
}


def main_cli():
    target = os.environ.get('INDIRAG_DATA_DIR')
    if not target:
        raise SystemExit('Set INDIRAG_DATA_DIR to a dedicated empty persistent directory first.')
    path = Path(target).resolve()
    if path.exists() and any(path.iterdir()):
        raise SystemExit('Refusing to seed a non-empty data directory.')
    import main
    from fastapi.testclient import TestClient
    # Seeding is a local administrative step; production auth still applies to live traffic.
    if main.AUTH_ENABLED:
        raise SystemExit('Run offline with INDIRAG_AUTH_ENABLED=false; restore production settings before serving.')
    client = TestClient(main.app)
    for filename, url in SOURCES.items():
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read(main.MAX_FILE_SIZE + 1)
        result = client.post('/api/documents/upload', files={'file': (filename, content, 'application/pdf')}, data={'collection_id': 'public-scholarship', 'collection_name': 'Public Scholarship'})
        result.raise_for_status()
        print(filename, 'indexed:', result.json()['passage_count'], 'passages')
    print('Newly generated document/passage IDs differ from the historical benchmark IDs.')


if __name__ == '__main__':
    main_cli()

"""Seed approved public PDFs into an explicitly configured, empty data directory."""
import os
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

SOURCES = {
    'FAQ_DOHE_CSSS.pdf': 'https://www.education.gov.in/sites/upload_files/mhrd/files/upload_document/FAQs_PM_USP2526.pdf',
    'Guidelines_DOHE_CSSS.pdf': 'https://www.education.gov.in/sites/upload_files/mhrd/files/upload_document/PM_USP_CSSS_guidelines.pdf',
}


def main_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--faq', type=Path, help='Local copy of the approved public FAQ PDF')
    parser.add_argument('--guidelines', type=Path, help='Local copy of the approved public guidelines PDF')
    args = parser.parse_args()
    if bool(args.faq) != bool(args.guidelines):
        raise SystemExit('Provide both --faq and --guidelines, or neither to download.')
    target = os.environ.get('INDIRAG_DATA_DIR')
    if not target:
        raise SystemExit('Set INDIRAG_DATA_DIR to a dedicated empty persistent directory first.')
    path = Path(target).resolve()
    if path.exists() and any(path.iterdir()):
        raise SystemExit('Refusing to seed a non-empty data directory.')
    if args.faq:
        documents = {name: path.read_bytes() for name, path in zip(SOURCES, (args.faq, args.guidelines))}
    else:
        documents = {}
        for filename, url in SOURCES.items():
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    documents[filename] = response.read(20 * 1024 * 1024 + 1)
            except OSError as exc:
                raise SystemExit(f'Unable to download {filename} ({type(exc).__name__}). Supply verified local PDFs using --faq and --guidelines.') from exc
    if any(len(content) > 20 * 1024 * 1024 or not content.startswith(b'%PDF-') for content in documents.values()):
        raise SystemExit('A source is not a PDF or exceeds 20 MB.')
    import main
    from fastapi.testclient import TestClient
    # Seeding is a local administrative step; production auth still applies to live traffic.
    if main.AUTH_ENABLED:
        raise SystemExit('Run offline with INDIRAG_AUTH_ENABLED=false; restore production settings before serving.')
    client = TestClient(main.app)
    manifest = []
    for filename, content in documents.items():
        result = client.post('/api/documents/upload', files={'file': (filename, content, 'application/pdf')}, data={'collection_id': 'public-scholarship', 'collection_name': 'Public Scholarship'})
        result.raise_for_status()
        print(filename, 'indexed:', result.json()['passage_count'], 'passages')
        manifest.append({'filename': filename, 'source_url': SOURCES[filename], 'sha256': hashlib.sha256(content).hexdigest(), 'input': 'local copy' if args.faq else 'download', 'document_id': result.json()['document']['doc_id']})
    (path / 'public-seed-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Newly generated document/passage IDs differ from the historical benchmark IDs.')


if __name__ == '__main__':
    main_cli()

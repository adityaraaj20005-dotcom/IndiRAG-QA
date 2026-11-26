"""Create disposable local PDFs for browser integration testing."""
from pathlib import Path
import pymupdf

root = Path(__file__).resolve().parents[2] / '.release-test'
folder = root / 'browser-fixtures' / 'FolderDemo'
folder.mkdir(parents=True, exist_ok=True)
for name, text in [('sample.pdf', 'Scholarship renewal requires 75 percent attendance.'), ('second.pdf', 'Annual scholarship is twelve thousand rupees.')]:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(folder / name)
    doc.close()
print('Disposable fixtures created under .release-test/browser-fixtures.')

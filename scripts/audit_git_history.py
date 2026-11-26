"""Scan all reachable Git blobs without printing matching values."""
import re
import subprocess
from collections import defaultdict

listing = subprocess.check_output(['git', 'rev-list', '--objects', '--all'], text=True, encoding='utf-8')
objects = {}
for line in listing.splitlines():
    oid, _, path = line.partition(' ')
    if path:
        objects.setdefault(oid, set()).add(path)
patterns = {
    'Google API key pattern': re.compile(rb'AIza[0-9A-Za-z_-]{30,}'),
    'GitHub token pattern': re.compile(rb'gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}'),
    'AWS access key pattern': re.compile(rb'AKIA[0-9A-Z]{16}'),
    'Private key header': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}
findings = defaultdict(set)
for oid, paths in objects.items():
    kind = subprocess.check_output(['git', 'cat-file', '-t', oid], text=True).strip()
    if kind != 'blob':
        continue
    for path in paths:
        lower = path.lower().replace('\\', '/')
        if (lower.endswith('.pdf') or '/.venv/' in lower or '/node_modules/' in lower or '/data/raw/' in '/' + lower or '/data/processed/' in '/' + lower or re.search(r'(^|/)\.env$', lower)):
            findings['Sensitive or generated path'].add(path)
    data = subprocess.check_output(['git', 'cat-file', 'blob', oid])
    for label, pattern in patterns.items():
        if pattern.search(data):
            findings[label].update(paths)
print('Reachable named blobs examined:', len(objects))
if findings:
    for label, paths in findings.items():
        print(label + ':')
        for path in sorted(paths):
            print('  ', path)
else:
    print('No matches for selected credential patterns or excluded path categories.')
print('Limitations: pattern scan is not a comprehensive secret or personal-data audit.')

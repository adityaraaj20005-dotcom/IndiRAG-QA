"""Export public aggregate results for the static, quota-free demonstration."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'frontend/public/research'
out.mkdir(parents=True, exist_ok=True)
retrieval = json.loads((root / 'research/results/retrieval_source_checked.json').read_text(encoding='utf-8'))
retrieval.pop('cases', None)
qa = json.loads((root / 'research/results/qa_smoke_corrected.json').read_text(encoding='utf-8'))
qa['records'] = {k: {'status': v['status'], 'pipeline': v['pipeline']} for k, v in qa['records'].items()}
for pipeline in qa['pipelines'].values():
    pipeline.pop('predictions', None)
for name, obj in [('retrieval.json', retrieval), ('qa-partial.json', qa)]:
    (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
print('Exported aggregates only; no documents, evidence text or credentials.')

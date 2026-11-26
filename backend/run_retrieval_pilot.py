"""Evaluate source-checked rows locally without invoking a generation API."""
import json
from datetime import datetime, timezone
from pathlib import Path
import main

ROOT = Path(__file__).resolve().parents[1]


def main_cli():
    source = ROOT / 'research/datasets/qa_pilot_smoke.json'
    candidates = ROOT / 'research/datasets/qa_candidates.json'
    rows = [r for path in (source, candidates) for r in json.loads(path.read_text(encoding='utf-8')) if r['answerable']]
    if len({r['question'].casefold().strip() for r in rows}) != len(rows):
        raise ValueError('Duplicate questions')
    parsed = [main.EvaluationRow(**r) for r in rows]
    result = main.run_evaluation(parsed)
    result['dataset'] = {'pilot_answerable': 9, 'candidate_answerable': 6, 'total': len(rows), 'annotation': 'source-checked; not independently human-reviewed', 'family_warning': 'translated variants share facts'}
    result['generated_at'] = datetime.now(timezone.utc).isoformat()
    result['cases'] = []
    for row in rows:
        evidence = main.retrieve(row['question'], main.scoped_passages(row['collection_id']), 'Hybrid', 5, main.get_embedding_model, main.get_dense_embeddings)
        result['cases'].append({'question': row['question'], 'language': row['language'], 'family_id': row.get('family_id'), 'gold_passage_ids': row['relevant_passage_ids'], 'returned_passage_ids': [p['passage_id'] for p in evidence], 'hit': any(p['passage_id'] in row['relevant_passage_ids'] for p in evidence)})
    output = ROOT / 'research/results/retrieval_source_checked.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved retrieval-only evaluation:', output)


if __name__ == '__main__':
    main_cli()

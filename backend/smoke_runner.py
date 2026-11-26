"""Resumable quota-limited smoke runner. One API call per missing prediction."""
import hashlib
import json
import os
import time
from pathlib import Path

import main
from direct_llm import generate_direct, generate_with_evidence
from qa_evaluation import summarize, by_language

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'research/datasets/qa_pilot_smoke.json'
OUTPUT = ROOT / 'research/results/qa_smoke_resumable.json'
LIMIT = 24


def save(path, state):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    for attempt in range(5):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.25 * (attempt + 1))


def run(rows, state, path, generate, max_failures=2):
    """Reserve each request durably before sending. Never retry interrupted calls."""
    if state.get('stop_reason', '').startswith('circuit breaker'):
        return state
    consecutive = 0
    for index, row in enumerate(rows):
        for pipeline in ('direct', 'rag'):
            key = f'{index}:{pipeline}'
            if key in state['records']:
                continue
            if state['request_count'] >= LIMIT:
                state['stop_reason'] = 'request budget exhausted'
                save(path, state)
                return state
            state['request_count'] += 1
            state['records'][key] = {'status': 'interrupted', 'question_index': index, 'pipeline': pipeline}
            save(path, state)
            try:
                result = generate(row, pipeline)
                state['records'][key] = {**row, **result, 'status': 'ok', 'question_index': index, 'pipeline': pipeline}
                consecutive = 0
            except Exception as exc:
                code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
                state['records'][key] = {**row, 'status': 'error', 'question_index': index, 'pipeline': pipeline, 'error_type': type(exc).__name__, 'http_status': code}
                consecutive += 1
                if code in (401, 403, 404, 429) or consecutive >= max_failures:
                    state['stop_reason'] = f'circuit breaker: HTTP {code}' if code else 'circuit breaker: repeated failures'
                    save(path, state)
                    return state
            save(path, state)
    state['stop_reason'] = 'complete'
    save(path, state)
    return state


def main_cli():
    rows = json.loads(DATASET.read_text(encoding='utf-8'))
    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    if OUTPUT.exists():
        state = json.loads(OUTPUT.read_text(encoding='utf-8'))
        pending = OUTPUT.with_suffix('.tmp')
        if pending.exists():
            recovered = json.loads(pending.read_text(encoding='utf-8'))
            if recovered['request_count'] > state['request_count']:
                state = recovered
        if state['dataset_sha256'] != digest:
            raise ValueError('Dataset changed; refusing to resume.')
    else:
        # Three previous calls allowed up to three attempts each; reserve the worst case.
        probe = json.loads((ROOT / 'research/results/qa_smoke_probe.json').read_text(encoding='utf-8'))
        state = {'dataset_sha256': digest, 'request_count': 9, 'historical_requests': 'Three calls, each with up to three attempts; retry counts were not recorded. Nine attempts conservatively reserved.', 'records': {}}
        for pipeline in ('direct', 'rag'):
            state['records'][f'0:{pipeline}'] = {**rows[0], **probe[pipeline], 'status': 'ok', 'question_index': 0, 'pipeline': pipeline, 'evidence': [], 'evidence_note': 'Evidence text was not retained in the original probe.'}
        save(OUTPUT, state)
    main.validate_qa_rows([main.QAEvaluationRow(**row) for row in rows])
    def generate(row, pipeline):
        if pipeline == 'direct':
            return {**generate_direct(row['question'], retries=0), 'evidence': [], 'citation_valid': None}
        evidence = main.retrieve(row['question'], main.scoped_passages(row['collection_id']), 'Hybrid', 5, main.get_embedding_model, main.get_dense_embeddings)
        response = generate_with_evidence(row['question'], evidence, retries=0)
        ids = {p['passage_id'] for p in evidence}
        citations = response.get('citations', [])
        return {**response, 'evidence': evidence, 'citation_valid': isinstance(citations, list) and bool(citations) and all(isinstance(c, str) and c in ids for c in citations)}
    run(rows, state, OUTPUT, generate)
    for pipeline in ('direct', 'rag'):
        predictions = [p for p in state['records'].values() if p['pipeline'] == pipeline and p['status'] != 'interrupted']
        state.setdefault('pipelines', {})[pipeline] = {'aggregate': summarize(predictions), 'language_wise': by_language(predictions), 'predictions': predictions}
    save(OUTPUT, state)
    print('Experiment state saved:', OUTPUT, 'status:', state.get('stop_reason'))


if __name__ == '__main__':
    main_cli()

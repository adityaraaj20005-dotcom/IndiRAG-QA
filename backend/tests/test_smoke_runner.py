import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smoke_runner import run
from qa_evaluation import summarize


def test_circuit_breaker_and_resume(tmp_path):
    path = tmp_path / 'result.json'
    state = {'request_count': 0, 'records': {}}
    class RateLimit(Exception):
        code = 429
    def fail(row, pipeline):
        raise RateLimit()
    run([{'question': 'q'}], state, path, fail)
    assert state['request_count'] == 1
    assert state['stop_reason'] == 'circuit breaker: HTTP 429'
    assert json.loads(path.read_text(encoding='utf-8'))['records']['0:direct']['status'] == 'error'


def test_generation_failure_not_abstention():
    result = summarize([{'status': 'error', 'answerable': True}])
    assert result['generation_failures'] == 1
    assert result['answerability']['false_negatives'] == 0
    assert result['answerability']['accuracy'] is None


def test_budget_prevents_request(tmp_path):
    state = {'request_count': 24, 'records': {}}
    run([{'question': 'q'}], state, tmp_path / 'r.json', lambda *a: 1 / 0)
    assert state['stop_reason'] == 'request budget exhausted'

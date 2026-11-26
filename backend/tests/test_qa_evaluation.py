from backend.qa_evaluation import exact_match, run_pipeline, token_f1


def test_unicode_normalization_and_multiple_references():
    assert exact_match("  ₹ 2,50,000 ", ["Rs 250000", "₹ 2,50,000"]) == 1
    assert exact_match("नहीं", ["हाँ", "नहीं"]) == 1
    assert token_f1("minimum attendance 75 percent", ["75 percent minimum attendance"]) == 1


def test_failure_is_not_counted_as_unanswerable():
    rows = [{"question": "q1", "language": "English", "answerable": True, "reference_answers": ["answer"]}, {"question": "q2", "language": "Hindi", "answerable": False, "reference_answers": []}]
    def runner(row):
        if row["question"] == "q1":
            raise TimeoutError("network")
        return {"answerability": "UNANSWERABLE", "answer": "", "latency_ms": 2, "citation_valid": None}
    result = run_pipeline(rows, runner)
    assert result["aggregate"]["generation_failures"] == 1
    assert result["aggregate"]["answerability"]["true_negatives"] == 1

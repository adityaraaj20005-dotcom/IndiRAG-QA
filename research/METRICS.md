# Metrics

`/api/evaluation/run` remains retrieval-only and reports Recall@K, Precision@K, Hit Rate, and MRR@K against verified passage IDs.

`/api/evaluation/qa` reports Exact Match, maximum token-level F1 over acceptable references, mean response latency, generation-failure count, citation-ID validity, and answerability accuracy/precision/recall/F1 with TP/TN/FP/FN. Text is NFC-normalized and Unicode-tokenized. Operational errors are excluded from scoring rather than silently counted as unanswerable predictions.

Citation validity means every returned citation ID is in the retrieved evidence. It does not establish semantic entailment. Unsupported-answer rate is intentionally absent until a manual support annotation is supplied.

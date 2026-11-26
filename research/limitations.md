# Limitations

- The present source collection supports a 12-row retrieval pilot, not a 300–500 item manually verified QA benchmark.
- No live QA result is bundled because producing one consumes Gemini quota and requires verified reference answers.
- Citation-ID validation is structural; human review is needed for evidence entailment and unsupported-answer labels.
- Sentence Transformers increases cold-start time and memory use. Deploy on a host with adequate RAM and persistent document storage.
- The partial smoke run includes only answerable examples. Direct calls included an empty passages field, potentially encouraging abstention; do not interpret this as a fair direct-model baseline. One RAG call failed with HTTP 503 and an interrupted reservation was excluded. The earlier retry count is unknown, so the request budget reserves its worst case.

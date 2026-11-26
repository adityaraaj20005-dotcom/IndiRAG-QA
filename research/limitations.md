# Limitations

- The present source collection supports a 12-row retrieval pilot, not a 300–500 item manually verified QA benchmark.
- No live QA result is bundled because producing one consumes Gemini quota and requires verified reference answers.
- Citation-ID validation is structural; human review is needed for evidence entailment and unsupported-answer labels.
- Sentence Transformers increases cold-start time and memory use. Deploy on a host with adequate RAM and persistent document storage.

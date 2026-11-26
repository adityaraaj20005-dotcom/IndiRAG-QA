# Faculty presentation: 14-slide outline

1. Title, Bennett University, course, team and research question.
2. Problem: evidence access across English, Hindi and Hinglish.
3. Motivation and limitations of unaided answers.
4. Architecture: PDF → passages → retrieval → evidence → optional generation.
5. Corpus and provenance: two public scholarship sources, page-level passages.
6. Retrieval methods: BM25, TF-IDF, multilingual MiniLM, BM25+dense RRF.
7. QA and citation validation: ID membership versus semantic support.
8. Dataset: 12 pilot questions plus six candidates; five answerable fact families, no independent review.
9. Retrieval experiment: methodology, K=5 and family-relatedness caveat.
10. Measured retrieval table: Hybrid Recall@5 0.8000 and MRR@5 0.5889, with baseline comparisons.
11. Partial QA: nine matched answerable pairs, RAG F1 0.250, Direct 0; interrupted by 429; no completed unanswerable cases.
12. Difficult cases: multilingual ranking and alternate supporting passages; do not equate gold-ID misses with factual failure.
13. Demonstration: retrieval-only workspace, source pages, four-method lab and saved result views.
14. Limitations, future work, verified references and questions: incomplete 300–500 benchmark, limited facts, no independent review, incomplete QA and support analysis.

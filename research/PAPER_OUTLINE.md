# IEEE-style paper outline: IndiRAG-QA

This is an outline for a paper of at least six pages, not a claim that the study is complete. Use the current IEEE conference template, confirm page limits with faculty, and cite verified sources only.

## Abstract (approximately 150–200 words)

Motivate evidence-grounded QA for English, Hindi and Hinglish. Summarize the PDF pipeline and retrieval comparison. Report the 15-question retrieval-only Hybrid Recall@5 of 0.8000 with the small, related-family sample caveat. Describe the QA results as incomplete and avoid a hallucination-reduction claim.

## I. Introduction

Explain cross-lingual access to scholarship guidance, code-mixed queries, and why page-level evidence matters. State the research question, contributions and limits. Identify the local corpus as a public scholarship-document demonstration, not all Indic languages or policies.

## II. Literature review

Discuss lexical retrieval, multilingual sentence embeddings, reciprocal rank fusion, retrieval-augmented generation, answerability and citation evaluation. Add independently verified primary-source citations for every method and comparison. Do not use placeholder or invented references.

## III. Problem statement

Define question, collection, passages, top-K evidence, answer and citation identifiers. Distinguish whether a document contains an answer from whether an unaided model knows one. Explain code-mixing, transliteration and missing or conflicting evidence.

## IV. System architecture

Describe Vite frontend, FastAPI, PyMuPDF extraction, overlapping page passages, persistent storage, collection filters, BM25, TF-IDF, multilingual MiniLM, BM25+dense RRF, Gemini generation and citation-ID validation. Include a system diagram and a statement that ID validity does not establish semantic support.

## V. Methodology

Specify passage indexing, language labels, exact-match and Unicode token F1, Recall@5, Precision@5, Hit Rate@5, MRR@5, answerability confusion matrix, latency and error exclusion. Explain direct versus RAG prompts, shared model, matched-sample analysis, and dataset family grouping. State API-failure and rate-limit handling.

## VI. Dataset

Report 12 source-checked QA pilot questions: three answerable examples per language and three unanswerable examples, one per language. Six additional source-checked candidates make 18 total. The 15 answerable variants cover five fact families. Cite official source URLs in `datasets/qa_pilot_evidence.md`. Disclose that no independent human annotation review occurred, and that the recommended 300–500-instance benchmark remains incomplete. Discuss source coverage, passage-ID validation and family-level split controls.

## VII. Experimental setup

Describe the indexed scholarship collection, K=5, retrieval-only run and result file `results/retrieval_source_checked.json`. Note that the historical pilot uses a different benchmark and must not be merged without explanation. Record model name, software versions, hardware, seeds and timing where verified. State that the Gemini run stopped at HTTP 429 after nine matched answerable pairs; no unanswerable question completed.

## VIII. Results

Include the measured retrieval table: BM25 recall/precision/hit/MRR 0.6667/0.1333/0.6667/0.4889; TF-IDF 0.6667/0.1333/0.6667/0.4389; Dense 0.7333/0.1467/0.7333/0.5167; Hybrid 0.8000/0.1600/0.8000/0.5889. For matched QA pairs, Direct and RAG EM are both 0; token F1 is 0 and 0.250; RAG citation IDs are valid in 9/9. Report coverage and the failed 429 request separately. Avoid generalizing from this small related sample.

## IX. Difficult-case analysis

Use `difficult_cases.md` and saved case traces: Hindi and Hinglish income gold-ID misses also retrieved corroborating guideline evidence; Hindi marks/duration had lower gold ranks; verbose numeric answers reduce short-reference EM. Distinguish retrieved-passage analysis from generated-answer analysis. The 15 retrieval queries are only five fact families and do not establish 15 independent error modes.

## X. Limitations and ethical considerations

Discuss incomplete 300–500 target, narrow source/fact diversity, no independent annotation review, incomplete QA and unanswerable evaluation, uncalibrated answerability, missing semantic citation support judgments, OCR and informal spelling limitations, prompt injection, and the shared-team security model.

## XI. Future work and conclusion

Propose diverse public documents, independent annotation, family-disjoint splits, completed quota-aware paired evaluation, blinded citation-support analysis, and robust multilingual robustness tests. Summarize actual results without claims of causality or proven hallucination reduction.

## Reference requirements

List the actual official scholarship PDFs and verified primary literature for BM25, TF-IDF, sentence embeddings, RRF, RAG and metrics, with complete bibliographic details and access dates. Verify publication metadata before submission. Do not invent citations, DOIs or benchmark references.

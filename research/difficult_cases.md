# Difficult-case review workflow

Review the actual `predictions` and `evidence` in `results/qa_smoke_resumable.json`. For each selected case, record question, reference answers, retrieved passage IDs and text, direct and RAG answers, citations, outcome, error category, and an evidence-based explanation. Categories include retrieval failure, language mismatch, unsupported answer, invalid citation, and successful abstention. Do not infer semantic support from citation-ID validity alone.

Fifteen-case target: pending independent review. The first paired English question in `qa_smoke_probe.json` was an observed direct abstention and RAG answer; the original evidence trace was not saved in that probe. Remaining cases must be selected and analyzed from the retained records.

## Corrected run: observed cases

The following observations refer to the nine matched pairs in `results/qa_smoke_corrected.json`; all were document-answerable. The JSON contains the full question, reference, prediction and retrieved evidence. They have not been independently adjudicated.

1. **English income, index 0:** expected Rs. 4.5 lakh per annum. Direct abstained without source context; RAG gave Rs. 4.5 lakh and cited `d03cd512b5b8_P2_C1` and `cf525ca294ba_P1_C2`. EM was zero despite the correct number because the answer was a full sentence.
2. **English attendance, index 1:** expected 75%. Direct abstained; RAG answered 75% and cited `cf525ca294ba_P2_C2` and `d03cd512b5b8_P2_C2`. This illustrates the sensitivity of token F1 to a verbose answer.
3. **Hindi income, index 3:** expected 4.5 lakh rupees annually. Direct abstained; RAG answered in Hindi with the amount, citing `d03cd512b5b8_P2_C1`. This is a cross-lingual retrieval success against English evidence.
4. **Hinglish income, index 6:** expected 4.5 lakh. Direct abstained; RAG returned the amount in English and cited `d03cd512b5b8_P2_C1`. The numeric fact is supported, but the response language did not match the code-mixed query.
5. **Hinglish attendance, index 7:** expected 75%. Direct abstained; RAG returned 75% in a mixed-language answer citing the FAQ and guidelines passages.

Four additional matched cases are available, but are variants of the same three fact families. No unanswerable case was completed; no successful abstention or invalid citation is claimed. The target of 15 distinct analyzed cases remains unmet.

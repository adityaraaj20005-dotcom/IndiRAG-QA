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

## Retrieval-only case traces

The 15 source-checked answerable questions, their Hybrid top-five passage IDs, and gold-ID hit flags are recorded individually in `results/retrieval_source_checked.json` under `cases`. Twelve hit their listed FAQ gold passage. The Hindi income and Hinglish income queries missed that specific gold ID but returned `d03cd512b5b8_P2_C1`, which also states the income limit; those are annotation-coverage limitations, not established factual retrieval failures. Hinglish marks missed FAQ `cf525ca294ba_P2_C2` but returned the guidelines' `d03cd512b5b8_P2_C2`, requiring source review before declaring failure. Hindi duration found its gold passage at rank four; Hindi marks at rank four; the English and Hindi undergraduate-rate questions found their gold at rank one. These observations concern retrieval IDs only and are not newly generated answers. Spelling, ambiguous, date, and named-entity cases remain unevaluated.

The following lists each genuinely evaluated retrieval case; rank is for the listed gold passage, not for all potentially relevant evidence. Full questions and ranked IDs are in the result JSON.

| Family | English | Hindi | Hinglish | Interpretation |
|---|---:|---:|---:|---|
| Income | 3 | miss | miss | Both misses returned the corroborating guideline; gold coverage is incomplete. |
| Attendance | 1 | 2 | 2 | Gold was retrieved in all variants; Hindi and Hinglish were ranked second. |
| Marks | 1 | 4 | miss | Hindi ranks the FAQ fourth; the Hinglish miss returned the guideline passage. |
| Undergraduate rate | 1 | 1 | 1 | The FAQ rate passage ranked first in each variant. |
| Duration | 1 | 4 | 1 | The Hindi gold result appears lower than the two Latin-script variants. |

This table contains 15 evaluated query cases but only five underlying fact families; it is not evidence of 15 independent failure modes. Entries are preliminary observations, not human-reviewed causal diagnoses.

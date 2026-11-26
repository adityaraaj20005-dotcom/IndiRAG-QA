import re

def detect_language(text):
    # Transparent heuristic, not a trained language classifier.
    if re.search(r'[\u0900-\u097f]',text):
        return 'Hindi-English mixed' if re.search(r'[A-Za-z]{2,}',text) else 'Hindi (Devanagari)'
    words=set(re.findall(r'[a-z]+',text.lower()))
    markers={'kya','kaise','kitna','kitni','kitne','liye','hai','hain','chahiye','mein','mera','meri','ka','ki','ke','kab','kahan','batao','hoga','hogi','nahi','karna','mujhe'}
    return 'Hinglish (heuristic)' if len(words & markers)>=2 else 'English / undetermined Latin script'

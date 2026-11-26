"""Scoped lexical, dense and reciprocal-rank fusion retrieval."""
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
import unicodedata

def tokenize(text):
    words=[]; word=''
    for c in unicodedata.normalize('NFC', text).casefold():
        if unicodedata.category(c)[0] in 'LMN': word+=c
        elif word: words.append(word); word=''
    if word: words.append(word)
    return words

def retrieve(question, items, method, top_k, model_getter, embeddings_getter):
    if not items: return []
    texts=[p['text'] for p in items]; tokens=tokenize(question)
    corpus=[tokenize(t) for t in texts]
    lexical_candidates=[i for i,t in enumerate(corpus) if set(tokens).intersection(t)]
    def rank(scores, candidates):
        return sorted(candidates,key=lambda i:(-float(scores[i]),i))
    if method in ('BM25','Hybrid'):
        bm=np.asarray(BM25Okapi(corpus).get_scores(tokens)) if any(corpus) else np.zeros(len(items))
        br=rank(bm,lexical_candidates)
    if method in ('Dense','Hybrid'):
        model=model_getter(); vectors=embeddings_getter(items)
        q=model.encode([question],normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)[0]
        ds=np.asarray(vectors @ q); dr=rank(ds,range(len(items)))
    if method=='TF-IDF':
        if not lexical_candidates: return []
        v=TfidfVectorizer(tokenizer=tokenize,token_pattern=None,lowercase=False)
        matrix=v.fit_transform(texts); scores=(matrix @ v.transform([question]).T).toarray().ravel(); order=rank(scores,lexical_candidates)
    elif method=='BM25': scores,order=bm,br
    elif method=='Dense': scores,order=ds,dr
    elif method=='Hybrid':
        scores=np.zeros(len(items))
        for ranking in (br,dr):
            for r,i in enumerate(ranking,1): scores[i]+=1/(60+r)
        order=rank(scores,set(br)|set(dr))
    else: raise ValueError('Unknown retrieval method')
    result=[]; seen=set()
    for i in order:
        p=items[i]; key=' '.join(p['text'].split())
        if key in seen: continue
        seen.add(key)
        row=dict(passage_id=p['passage_id'],doc_id=p['doc_id'],source=p['document_name'],page=p['page'],text=p['text'],collection_id=p.get('collection_id','uploaded-pdfs'),collection_name=p.get('collection_name','Uploaded PDFs'),score=round(float(scores[i]),5))
        if method=='BM25': row['bm25_score']=row['score']
        result.append(row)
        if len(result)>=top_k: break
    return result

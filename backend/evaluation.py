"""Retrieval metrics over manually labeled passage IDs; no invented results."""
def metrics(ranked, relevant, k=5):
    relevant=set(relevant); ranked=list(dict.fromkeys(ranked))[:k]
    if not relevant: raise ValueError('Retrieval metrics require at least one relevant passage')
    hits=[i for i,p in enumerate(ranked,1) if p in relevant]
    return {'recall':len(hits)/len(relevant),'precision':len(hits)/k,'hit_rate':float(bool(hits)),'mrr_at_k':1/hits[0] if hits else 0.0}

def evaluate(rows, retrieve_fn, methods=('BM25','Dense','Hybrid','TF-IDF'), k=5):
    output=[]
    for method in methods:
        groups={}
        for row in rows:
            if not row.get('relevant_passage_ids'): continue
            evidence=retrieve_fn(row,method,k)
            values=metrics([p['passage_id'] for p in evidence],row['relevant_passage_ids'],k)
            for name in {'all',row.get('language','unknown')}: groups.setdefault(name,[]).append(values)
        for name,values in groups.items():
            output.append({'method':method,'language':name,'n':len(values),'k':k,**{key:sum(v[key] for v in values)/len(values) for key in values[0]}})
    return output

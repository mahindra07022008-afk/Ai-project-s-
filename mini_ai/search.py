"""PocketSearch: TF-IDF retrieval with matching-term explanations."""
from collections import Counter
from .core import cosine, fit_vectors, tokens, vector


class PocketSearch:
    def __init__(self, documents):
        self.documents = list(documents)
        self.vectors, self.idf = fit_vectors(self.documents)

    def search(self, query, limit=3):
        if limit < 1:
            raise ValueError('limit must be positive')
        q = vector(Counter(tokens(query)), self.idf)
        results = []
        for index, doc in enumerate(self.vectors):
            score = cosine(q, doc)
            if score > 0:
                terms = sorted(set(q) & set(doc), key=lambda w: (-q[w] * doc[w], w))
                results.append({'document': index + 1, 'text': self.documents[index],
                                'score': round(score, 6), 'matched_terms': terms})
        return sorted(results, key=lambda r: (-r['score'], r['document']))[:limit]

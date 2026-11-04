"""TraceBrief: extractive summarization with source sentence numbers."""
import re
from .core import cosine, fit_vectors


def summarize(text, count=3):
    if count < 1:
        raise ValueError('count must be positive')
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]
    if not sentences:
        return []
    vectors, _ = fit_vectors(sentences)
    centrality = [sum(cosine(v, other) for j, other in enumerate(vectors) if j != i)
                  for i, v in enumerate(vectors)]
    selected = []
    for _ in range(min(count, len(sentences))):
        remaining = [i for i in range(len(sentences)) if i not in selected]
        # Penalize repetition while preferring sentences related to the document.
        def rank(i):
            relevance = centrality[i] / max(1, len(sentences) - 1)
            redundancy = max((cosine(vectors[i], vectors[j]) for j in selected), default=0)
            return (0.7 * relevance - 0.3 * redundancy, -i)
        selected.append(max(remaining, key=rank))
    return [{'sentence': i + 1, 'text': sentences[i]} for i in sorted(selected)]

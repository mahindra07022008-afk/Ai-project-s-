"""InboxLens: multinomial Naive Bayes with a review fallback."""
import math
from collections import Counter, defaultdict
from .core import tokens


class InboxLens:
    def __init__(self, examples):
        self.words = defaultdict(Counter)
        self.counts = Counter()
        for row in examples:
            if not isinstance(row, dict) or not isinstance(row.get('label'), str) or not row['label'].strip() or not isinstance(row.get('text'), str):
                raise ValueError('Each training row needs a nonempty label and text strings')
            self.words[row['label']].update(tokens(row['text']))
            self.counts[row['label']] += 1
        self.vocabulary = set(w for counts in self.words.values() for w in counts)
        if len(self.counts) < 2 or not self.vocabulary:
            raise ValueError('Training needs at least two labels and some words')

    def predict(self, text, threshold=0.65):
        if not 0 <= threshold <= 1:
            raise ValueError('threshold must be between 0 and 1')
        bag = Counter(tokens(text))
        known = set(bag) & self.vocabulary
        if not known:
            return {'label': 'review', 'reason': 'No known training words', 'scores': {}, 'matched_terms': []}
        logits = {}
        for label, counts in self.words.items():
            denominator = sum(counts.values()) + len(self.vocabulary)
            logits[label] = math.log(self.counts[label] / self.counts.total()) + sum(
                bag[w] * math.log((counts[w] + 1) / denominator) for w in known)
        peak = max(logits.values())
        weights = {label: math.exp(value - peak) for label, value in logits.items()}
        total = sum(weights.values())
        scores = {label: value / total for label, value in weights.items()}
        winner = max(sorted(scores), key=scores.get)
        accepted = scores[winner] >= threshold
        return {'label': winner if accepted else 'review',
                'reason': 'Model score above threshold' if accepted else 'Ambiguous message',
                'scores': {k: round(v, 6) for k, v in sorted(scores.items())},
                'matched_terms': sorted(known)}

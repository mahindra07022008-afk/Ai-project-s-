"""Shared English tokenization and TF-IDF vector operations."""
import math
import re
from collections import Counter

STOP = set('a an the and or is are was were to of in on for with it this that be as at by'.split())


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower()) if w not in STOP]


def fit_vectors(texts):
    bags = [Counter(tokens(text)) for text in texts]
    df = Counter(word for bag in bags for word in bag)
    idf = {w: math.log((1 + len(bags)) / (1 + count)) + 1 for w, count in df.items()}
    return [vector(bag, idf) for bag in bags], idf


def vector(bag, idf):
    values = {w: (1 + math.log(n)) * idf[w] for w, n in bag.items() if w in idf and n > 0}
    norm = math.sqrt(sum(v * v for v in values.values()))
    return {w: v / norm for w, v in values.items()} if norm else {}


def cosine(left, right):
    return sum(value * right.get(word, 0) for word, value in left.items())

"""Recommend unseen products from anonymous basket co-occurrence."""
import argparse
import json
from pathlib import Path

def items(values):
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError("each basket and liked list must contain at most 100 product names")
    if any(not isinstance(x, str) or not x.strip() or len(x) > 100 for x in values):
        raise ValueError("product names must be nonempty strings up to 100 characters")
    return set(x.strip() for x in values)

def analyze(data):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    baskets = data.get("baskets")
    if not isinstance(baskets, list) or not 1 <= len(baskets) <= 1000:
        raise ValueError("baskets needs 1 to 1000 anonymous purchase baskets")
    baskets = [items(b) for b in baskets]
    liked = items(data.get("liked"))
    limit = data.get("limit", 5)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be an integer from 1 to 20")
    memberships = {}
    for index, basket in enumerate(baskets):
        for product in basket:
            memberships.setdefault(product, set()).add(index)
    known = liked & memberships.keys()
    recommendations = []
    for candidate in sorted(memberships.keys() - liked):
        evidence = []
        for product in sorted(known):
            overlap = len(memberships[candidate] & memberships[product])
            if overlap:
                similarity = overlap / len(memberships[candidate] | memberships[product])
                evidence.append({"liked_product": product, "shared_baskets": overlap,
                                 "jaccard": similarity})
        if evidence:
            score = sum(e["jaccard"] for e in evidence) / len(known)
            recommendations.append({"product": candidate, "score": round(score, 6),
                                    "evidence": evidence})
    recommendations.sort(key=lambda r: (-r["score"], r["product"]))
    return {"recommendations": recommendations[:limit],
            "unknown_products": sorted(liked - memberships.keys()),
            "status": "matched" if recommendations else "insufficient_overlap"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 2000000:
            raise ValueError("input exceeds 2 MB")
        result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()

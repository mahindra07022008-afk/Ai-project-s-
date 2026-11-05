"""Find candidate duplicate support tickets with TF-IDF; never merge automatically."""
import argparse
import json
import math
from pathlib import Path
from mini_ai.core import fit_vectors, cosine, tokens

def find_duplicates(tickets, threshold=0.65):
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError("threshold must be a finite number greater than 0 and at most 1")
    if not isinstance(tickets, list) or len(tickets) > 500:
        raise ValueError("provide a JSON array with at most 500 tickets")
    seen = set()
    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError("each ticket must be an object")
        ident, message = ticket.get("id"), ticket.get("text")
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError("ticket ids must be unique nonempty strings")
        if not isinstance(message, str) or not message.strip() or len(message) > 10000:
            raise ValueError("ticket text must contain 1 to 10000 characters")
        if not tokens(message):
            raise ValueError("ticket text must contain English words or numbers")
        seen.add(ident)
    vectors, _ = fit_vectors([t["text"] for t in tickets])
    pairs = []
    for i, left in enumerate(tickets):
        for j in range(i + 1, len(tickets)):
            score = min(1.0, max(0.0, cosine(vectors[i], vectors[j])))
            if score + 1e-12 >= threshold:
                pairs.append({"ticket_a": left["id"], "ticket_b": tickets[j]["id"],
                              "similarity": round(score, 6),
                              "shared_terms": sorted(set(vectors[i]) & set(vectors[j])),
                              "action": "human_review"})
    return sorted(pairs, key=lambda p: (-p["similarity"], p["ticket_a"], p["ticket_b"]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--threshold", type=float, default=0.65)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 6_000_000:
            raise ValueError("input file exceeds 6 MB")
        tickets = json.loads(args.input.read_text(encoding="utf-8"))
        pairs = find_duplicates(tickets, args.threshold)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps({"tickets_checked": len(tickets), "candidate_pairs": pairs}, indent=2))

if __name__ == "__main__":
    main()

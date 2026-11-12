"""Learn a robust normal range from reference sensor readings."""
import argparse
import json
import math
from pathlib import Path
from statistics import median

def numbers(values, name, minimum):
    if not isinstance(values, list) or not minimum <= len(values) <= 10000:
        raise ValueError(f"{name} needs {minimum} to 10000 readings")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 1e12 for v in values):
        raise ValueError(f"{name} must contain finite numbers within +/- 1 trillion")

def analyze(data):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    reference, readings = data.get("reference"), data.get("readings")
    numbers(reference, "reference", 5)
    numbers(readings, "readings", 1)
    threshold = data.get("threshold", 3.5)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold <= 100:
        raise ValueError("threshold must be greater than 0 and at most 100")
    center = median(reference)
    deviation = median([abs(x - center) for x in reference])
    results = []
    for i, value in enumerate(readings):
        gap = abs(value - center)
        score = None
        if deviation:
            score = 1e300 if gap > deviation * 1e300 else 0.67448975 * gap / deviation
        flag = score > threshold if score is not None else value != center
        results.append({"row": i + 1, "value": value, "anomaly": flag,
                        "score": round(score, 4) if score is not None else None})
    return {"median": center, "mad": deviation,
            "rule": "modified_z_score" if deviation else "zero_mad_any_deviation",
            "anomaly_count": sum(r["anomaly"] for r in results), "readings": results}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 1000000:
            raise ValueError("input exceeds 1 MB")
        result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()

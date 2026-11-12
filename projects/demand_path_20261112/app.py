"""Learn a daily demand trend and compare it with a last-value baseline."""
import argparse
import json
import math
from pathlib import Path

def predict(history, steps):
    center = (len(history) - 1) / 2
    average = sum(history) / len(history)
    slope = sum((i - center) * (y - average) for i, y in enumerate(history))
    slope /= sum((i - center) ** 2 for i in range(len(history)))
    return [max(0.0, average + slope * (len(history) + i - center)) for i in range(steps)]

def analyze(data):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    values = data.get("daily_units")
    horizon = data.get("horizon", 3)
    if not isinstance(values, list) or not 6 <= len(values) <= 1000:
        raise ValueError("daily_units needs 6 to 1000 consecutive daily observations")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1e9 for v in values):
        raise ValueError("units must be finite numbers between 0 and 1 billion")
    if type(horizon) is not int or not 1 <= horizon <= 30:
        raise ValueError("horizon must be an integer from 1 to 30")
    split = max(3, len(values) - min(7, len(values) // 3))
    actual = values[split:]
    trend = predict(values[:split], len(actual))
    trend_error = sum(abs(a - b) for a, b in zip(actual, trend)) / len(actual)
    baseline_error = sum(abs(a - values[split - 1]) for a in actual) / len(actual)
    use_trend = trend_error < baseline_error
    forecast = predict(values, horizon) if use_trend else [values[-1]] * horizon
    return {"method": "linear_trend" if use_trend else "last_value",
            "validation_days": len(actual), "trend_mae": round(trend_error, 4),
            "baseline_mae": round(baseline_error, 4),
            "forecast_units": [round(x, 4) for x in forecast]}

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

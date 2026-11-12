import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from projects.demand_path_20261112.app import analyze as forecast
from projects.sensor_scout_20261112.app import analyze as detect
from projects.basket_bridge_20261112.app import analyze as recommend

class DemandTests(unittest.TestCase):
    def test_known_trend_and_holdout(self):
        result = forecast({"daily_units":[10,12,14,16,18,20,22,24,26]})
        self.assertEqual(result["forecast_units"], [28,30,32])
        self.assertEqual(result["trend_mae"], 0)
        self.assertEqual(result["validation_days"], 3)

    def test_constant_chooses_baseline(self):
        self.assertEqual(forecast({"daily_units":[5]*9})["method"], "last_value")

    def test_decline_clamped(self):
        result = forecast({"daily_units":[9,8,7,6,5,4,3,2,1],"horizon":5})
        self.assertEqual(result["forecast_units"], [0]*5)

    def test_invalid_values(self):
        for value in [None, True, -1, float("nan"), float("inf"), 1e10, "4"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                forecast({"daily_units":[5]*8+[value]})

    def test_invalid_shapes(self):
        for data in [[], {}, {"daily_units":[1]*5}, {"daily_units":[1]*1001},
                     {"daily_units":[1]*6,"horizon":True},
                     {"daily_units":[1]*6,"horizon":31}]:
            with self.subTest(data=str(data)[:100]), self.assertRaises(ValueError):
                forecast(data)

class SensorTests(unittest.TestCase):
    def test_outlier_separate_reference(self):
        result = detect({"reference":[19,20,20,21,22,21,20],"readings":[20,21,45]})
        self.assertEqual(result["anomaly_count"],1)
        self.assertTrue(result["readings"][2]["anomaly"])
        self.assertEqual(result["median"],20)

    def test_zero_mad_policy(self):
        result = detect({"reference":[10]*5,"readings":[10,11]})
        self.assertEqual(result["rule"],"zero_mad_any_deviation")
        self.assertEqual(result["anomaly_count"],1)
        self.assertIsNone(result["readings"][1]["score"])

    def test_tiny_reference_spread_stays_json_safe(self):
        result = detect({"reference":[0, 5e-324, 1e-323, 1.5e-323, 2e-323],"readings":[100]})
        self.assertTrue(result["readings"][0]["anomaly"])
        json.dumps(result, allow_nan=False)

    def test_negative_normal_readings(self):
        result = detect({"reference":[-3,-2,-1,0,1],"readings":[-1]})
        self.assertFalse(result["readings"][0]["anomaly"])

    def test_invalid_values(self):
        for value in [True,None,"10",float("nan"),float("inf"),1e13]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                detect({"reference":[0]*5,"readings":[value]})

    def test_invalid_shape_threshold(self):
        for data in [{}, [], {"reference":[1],"readings":[1]},
                     {"reference":[1]*5,"readings":[]},
                     {"reference":[1]*5,"readings":[1],"threshold":0},
                     {"reference":[1]*5,"readings":[1],"threshold":float("nan")}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                detect(data)

class BasketTests(unittest.TestCase):
    def test_ranking_evidence(self):
        result = recommend({"baskets":[["book","pen"],["book","pen"],["book","bag"]],"liked":["book"]})
        self.assertEqual(result["recommendations"][0]["product"],"pen")
        self.assertEqual(result["recommendations"][0]["evidence"][0]["shared_baskets"],2)
        self.assertAlmostEqual(result["recommendations"][0]["score"],2/3,places=5)

    def test_duplicates_do_not_inflate(self):
        a = recommend({"baskets":[["book","pen"]],"liked":["book"]})
        b = recommend({"baskets":[["book","book","pen"]],"liked":["book","book"]})
        self.assertEqual(a,b)

    def test_unknown_and_empty_likes(self):
        for likes in [[],["unknown"]]:
            self.assertEqual(recommend({"baskets":[["book"]],"liked":likes})["recommendations"],[])

    def test_seen_products_excluded(self):
        result = recommend({"baskets":[["book","pen"]],"liked":["book","pen"]})
        self.assertEqual(result["recommendations"],[])

    def test_tie_deterministic(self):
        result = recommend({"baskets":[["book","b"],["book","a"]],"liked":["book"],"limit":1})
        self.assertEqual(result["recommendations"][0]["product"],"a")

    def test_invalid_inputs(self):
        for data in [[], {}, {"baskets":[],"liked":[]},
                     {"baskets":[[""]],"liked":[]},
                     {"baskets":[[5]],"liked":[]},
                     {"baskets":[["x"]],"liked":"x"},
                     {"baskets":[["x"]],"liked":[],"limit":0}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                recommend(data)

class ProjectCLITests(unittest.TestCase):
    def test_all_example_flows(self):
        for name in ["demand_path","sensor_scout","basket_bridge"]:
            folder = f"projects/{name}_20261112"
            result = subprocess.run([sys.executable, f"{folder}/app.py", f"{folder}/example.json"], capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIsInstance(json.loads(result.stdout),dict)

    def test_all_cli_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp)/"bad.json"
            file.write_text("{bad")
            for name in ["demand_path","sensor_scout","basket_bridge"]:
                result = subprocess.run([sys.executable,f"projects/{name}_20261112/app.py",str(file)],capture_output=True,text=True)
                self.assertEqual(result.returncode,2)
                self.assertIn("Error:",result.stderr)

    def test_inputs_not_mutated(self):
        cases = [(forecast,{"daily_units":[1,2,3,4,5,6]}),
                 (detect,{"reference":[1,2,3,4,5],"readings":[3]}),
                 (recommend,{"baskets":[["a","b"]],"liked":["a"]})]
        for function,data in cases:
            original = copy.deepcopy(data)
            function(data)
            self.assertEqual(data,original)

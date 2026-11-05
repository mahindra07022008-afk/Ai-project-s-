import json
import subprocess
import sys
import unittest
from projects.ticket_twin_20261106.app import find_duplicates

class TicketTwinTests(unittest.TestCase):
    def test_duplicates_and_unrelated(self):
        data = [{"id":"A","text":"payment charged twice refund"}, {"id":"B","text":"refund payment charged twice"}, {"id":"C","text":"change profile avatar"}]
        pairs = find_duplicates(data)
        self.assertEqual(len(pairs), 1)
        self.assertEqual((pairs[0]["ticket_a"], pairs[0]["ticket_b"]), ("A","B"))
        self.assertEqual(pairs[0]["similarity"], 1.0)
        self.assertIn("refund", pairs[0]["shared_terms"])

    def test_empty_single_and_unknown(self):
        self.assertEqual(find_duplicates([]), [])
        self.assertEqual(find_duplicates([{"id":"A","text":"hello"}]), [])
        self.assertEqual(find_duplicates([{"id":"A","text":"hello"},{"id":"B","text":"world"}]), [])

    def test_invalid_records(self):
        for data in [None, {}, [4], [{"id":"","text":"x"}], [{"id":"A","text":""}], [{"id":"A","text":"!!!"}], [{"id":"A","text":"a"*10001}], [{"id":"A","text":"hi"},{"id":"A","text":"bye"}], [{"id":1,"text":"hi"}]]:
            with self.subTest(data=str(data)[:100]), self.assertRaises(ValueError):
                find_duplicates(data)

    def test_invalid_threshold(self):
        for value in [0, -1, 1.01, float("nan"), float("inf"), True, "0.5"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                find_duplicates([], value)

    def test_limit(self):
        with self.assertRaises(ValueError):
            find_duplicates([{"id":str(i),"text":"hello"} for i in range(501)])

    def test_boundary_and_case(self):
        self.assertEqual(len(find_duplicates([{"id":"A","text":"LOGIN broken!"},{"id":"B","text":"login broken"}], 1)), 1)

    def test_cli_smoke(self):
        result = subprocess.run([sys.executable,"-m","projects.ticket_twin_20261106.app","projects/ticket_twin_20261106/tickets.json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["candidate_pairs"]), 1)

    def test_cli_missing_file(self):
        result = subprocess.run([sys.executable,"-m","projects.ticket_twin_20261106.app","missing-file.json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Error:", result.stderr)

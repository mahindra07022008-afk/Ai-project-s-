import json
import subprocess
import sys
import unittest
from mini_ai.search import PocketSearch
from mini_ai.triage import InboxLens
from mini_ai.brief import summarize

class Projects(unittest.TestCase):
    def test_search_ranking(self):
        r = PocketSearch(['solar battery power', 'python code', 'solar panels']).search('battery solar')
        self.assertEqual(r[0]['document'], 1)
        self.assertEqual(set(r[0]['matched_terms']), {'solar', 'battery'})
        self.assertTrue(0 < r[0]['score'] <= 1)
    def test_search_empty(self):
        for docs, query in [([], 'hello'), (['hello'], 'zebra'), ([''], '')]:
            self.assertEqual(PocketSearch(docs).search(query), [])
    def test_search_limit(self):
        with self.assertRaises(ValueError): PocketSearch([]).search('x', 0)
    def model(self):
        return InboxLens([{'label':'billing','text':'refund payment invoice'}, {'label':'technical','text':'crash error login'}])
    def test_classification(self):
        r = self.model().predict('refund invoice please')
        self.assertEqual(r['label'], 'billing')
        self.assertAlmostEqual(sum(r['scores'].values()), 1, places=5)
    def test_review(self):
        for message in ['unicorn', 'refund error', '']:
            self.assertEqual(self.model().predict(message)['label'], 'review')
    def test_invalid_training(self):
        for rows in [[], [3], [{'label':'a','text':''}]]:
            with self.assertRaises(ValueError): InboxLens(rows)
    def test_invalid_threshold(self):
        with self.assertRaises(ValueError): self.model().predict('refund', 2)
    def test_long_message(self):
        self.assertEqual(self.model().predict('refund ' * 10000)['label'], 'billing')
    def test_summary_evidence(self):
        sentences = ['Solar power is clean.', 'Solar panels make power.', 'Cats sleep.']
        r = summarize(' '.join(sentences), 2)
        self.assertEqual(len(r), 2)
        self.assertEqual([x['sentence'] for x in r], sorted(x['sentence'] for x in r))
        for item in r: self.assertEqual(item['text'], sentences[item['sentence'] - 1])
    def test_summary_edges(self):
        self.assertEqual(summarize(''), [])
        self.assertEqual(len(summarize('One sentence.', 10)), 1)
        with self.assertRaises(ValueError): summarize('hello', 0)
    def test_summary_repeatable(self):
        self.assertEqual(summarize('A. B. C.', 1), summarize('A. B. C.', 1))
    def test_cli_examples(self):
        for args in [('search','examples/notes.json','local automation'), ('triage','examples/training.json','refund payment'), ('brief','examples/article.txt')]:
            r = subprocess.run([sys.executable, '-m', 'mini_ai', *args], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(json.loads(r.stdout))
    def test_cli_missing_file(self):
        r = subprocess.run([sys.executable, '-m', 'mini_ai', 'brief', 'missing.txt'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn('Traceback', r.stderr)

if __name__ == '__main__': unittest.main()

# Mahindra's AI Projects

## Featured: two practical freelancer applications

| Project | What you can do |
| --- | --- |
| [ClientDesk](freelancer-suite/projects/clientdesk/README.md) | Save business policies, draft evidence-backed client replies, and track requests. |
| [ActionBoard](freelancer-suite/projects/actionboard/README.md) | Extract meeting commitments, edit tasks, track progress, and export CSV. |

**[Setup and complete documentation →](freelancer-suite/README.md)**

Both applications share a local Python + SQLite workspace with a responsive browser UI. Run `python app.py` inside `freelancer-suite`. Default workflows require no API keys or Python dependencies. Optional local AI extraction requires an installed Ollama model. 12 application tests passed locally; visual browser QA and live-model inference remain unverified.

---

## Earlier learning projects

# Small AI, Clear Evidence

**Three offline NLP mini-projects you can run, inspect, and extend.**

Built for Mahindra's portfolio with AI assistance. No API keys, paid services, model downloads, or third-party Python packages required. These are classical machine-learning / NLP projects, not generative chatbots.

| Project | Purpose | Technique | Evidence |
| --- | --- | --- | --- |
| **PocketSearch** | Search personal notes | TF-IDF + cosine similarity | Document number and matching terms |
| **InboxLens** | Classify short messages | Trainable multinomial Naive Bayes | Category scores and review fallback |
| **TraceBrief** | Summarize short articles | Sentence similarity with redundancy penalty | Exact excerpts with sentence numbers |

## Quick start

Install Python 3.10 or newer. Open a terminal in this extracted project folder:

```bash
python -m mini_ai search examples/notes.json "local automation"
python -m mini_ai triage examples/training.json "refund payment charged twice"
python -m mini_ai brief examples/article.txt --sentences 2
```

On Windows, use `py` instead of `python` if needed. No `pip install` step is needed. Each tool prints JSON and runs only when invoked. There are no network requests, scheduled jobs, or file modifications.

## PocketSearch

Use a UTF-8 JSON array of strings: each string is one document.

```bash
python -m mini_ai search examples/notes.json "solar energy" --limit 2
```

[Implementation](mini_ai/search.py): TF is `1 + log(count)`, IDF is `log((1 + document_count)/(1 + document_frequency)) + 1`. Normalized vectors are ranked with cosine similarity. Results contain original text, 1-based document numbers, similarity scores, and matching words. Unknown queries return an empty array. Scores measure lexical similarity, not correctness. All documents are indexed in memory on each run.

## InboxLens

Use a UTF-8 JSON array of objects containing `label` and `text` strings. Include at least two labels. The model trains locally on each invocation.

```bash
python -m mini_ai triage examples/training.json "login error app crashes" --threshold 0.8
```

[Implementation](mini_ai/triage.py): multinomial Naive Bayes uses Laplace smoothing, class priors, and log probabilities. Unknown words are ignored. Messages without recognized words or below the threshold return `review`. Scores are **not calibrated confidence estimates**. No messages are sent and no actions are performed.

The nine training examples are synthetic demo data. Add representative examples and evaluate on a separate labeled test set before real-world use. No production accuracy claim is made.

## TraceBrief

Provide a UTF-8 text file:

```bash
python -m mini_ai brief examples/article.txt --sentences 3
```

[Implementation](mini_ai/brief.py): sentence centrality is average TF-IDF cosine similarity to other sentences. Selection balances relevance (0.7) against similarity to already-selected sentences (0.3). Selected sentences are returned verbatim in source order with 1-based sentence numbers. Stable source order breaks ties. This extracts text; it does not generate new claims or fact-check the article.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover retrieval ranking and evidence, empty and unknown input, classification, review fallback, invalid inputs, long-message numerical stability, exact-source summaries, runnable CLI examples, and missing-file errors. GitHub Actions is configured for Python 3.10–3.13. Remote CI results must be checked after publishing.

## Limits and next experiments

- Tokenization and stop words are English-focused; other languages need a different tokenizer.
- Word overlap cannot recognize synonyms or deep meaning.
- Sentence splitting is simple; abbreviations can split incorrectly.
- Exact excerpts may still omit important context.
- Summarization compares sentence pairs: use short articles, not books.
- Keep private notes and training data out of public repositories.

Next experiments: compare search against embeddings, measure classification on held-out data with a confusion matrix, and compare summaries with human-selected key sentences. Publish actual measurements instead of unsupported benchmark claims.

## Files

- `mini_ai/`: shared utilities, three algorithms, and CLI.
- `examples/`: synthetic examples and sample article.
- `tests/`: automated functional tests.
- `.github/workflows/tests.yml`: continuous integration.

Created with AI assistance. Review the implementation and document what you learn as you extend it.

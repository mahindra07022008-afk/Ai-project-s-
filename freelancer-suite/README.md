# Freelance Studio

Two practical local applications for freelancers: **ClientDesk** handles recurring client questions; **ActionBoard** tracks commitments from meetings. Built with Python, SQLite, and a responsive browser interface. No Python packages or API keys are needed for the default workflows.

## Run in one step

Requires Python 3.10 or newer. Download the repository, open the `freelancer-suite` folder, and run:

```bash
python app.py
```

On Windows, double-click `start-windows.bat` (Python's `py` launcher must be installed), or run `py app.py`.

Open **http://127.0.0.1:8765** in your browser. Use the sidebar to switch projects. Stop with Ctrl+C. Your data remains in `workspace.db` after closing the app. The app runs while your computer is on; it has no background schedules.

| Project | Use case | Features |
| --- | --- | --- |
| [ClientDesk](projects/clientdesk/README.md) | Answer repetitive client questions from business policies | Local TF-IDF retrieval, quoted evidence, editable drafts, request status, policy library, search |
| [ActionBoard](projects/actionboard/README.md) | Turn meeting commitments into trackable work | Offline or optional local-AI extraction, source quotes, editable owners/dates, progress states, CSV export, original notes |

## Try it

**ClientDesk:** Choose Fill demo example → Add policy → Find policy & draft reply. Review the evidence, edit the draft, and mark the request resolved. Replies are never sent automatically.

**ActionBoard:** Open ActionBoard → Fill demo example → Extract action items. Edit task owners and dates, update progress, and download the CSV. Demo content is synthetic and only saved when you submit it.

## How the AI works

ClientDesk uses classical NLP: paragraph-level TF-IDF vectors and cosine similarity. It returns up to three relevant policy excerpts above a similarity threshold. Results are source quotations, not generated customer-ready prose. No-match cases explicitly request manual review. Matching words do not guarantee that the policy applies to the request.

ActionBoard has two clearly labeled modes:

- **Offline patterns:** detects lines such as `Action: Maya: Send proposal by 2026-12-15` and `Arjun will review navigation`. This is deterministic parsing, not a language model. It may misinterpret speaker labels; inspect all results.
- **Local AI:** sends notes to an Ollama model running at `127.0.0.1:11434`. The model returns JSON actions. The app verifies source quotations, removes owners/dates not present in those quotations, and rejects malformed or ungrounded output. Review is still required: quotation validation does not prove that an action title is accurate.

To enable local AI, install [Ollama](https://ollama.com/) and an appropriate local model, start Ollama, and set `OLLAMA_MODEL` to the exact installed model name before launching the app:

```powershell
# Windows PowerShell — substitute the model you installed
$env:OLLAMA_MODEL="YOUR_INSTALLED_MODEL_NAME"
py app.py
```

```bash
# macOS / Linux — substitute the model you installed
OLLAMA_MODEL=YOUR_INSTALLED_MODEL_NAME python3 app.py
```

Model installation is optional and may require substantial disk space and RAM. The default workflows work without it. Integration follows the [Ollama generate API](https://github.com/ollama/ollama/blob/main/docs/api.md): non-streaming JSON output. There is no cloud API integration or billing in this code.

## Architecture

Browser UI → local HTTP API → SQLite persistence / NLP engine.

- `app.py`: loopback-only HTTP server, validation, database operations, exports.
- `intelligence.py`: evidence retrieval and meeting extraction.
- `web/`: semantic HTML, responsive CSS, vanilla JavaScript.
- `tests/`: real HTTP integration tests and mocked model-output tests.

API routes: `GET /api/state`, `GET /api/export`; `POST /api/documents`, `/api/tickets`, `/api/meetings`, `/api/task`, `/api/ticket`, `/api/delete`. Mutation requests need the session token supplied by `/api/state`. The UI handles it automatically.

## Data and deployment boundaries

This is a **single-user local application**, not an internet-hosted multi-user service. The server binds to loopback, validates Host headers, uses a random session token for mutations, and emits restrictive browser headers. Text renders as text rather than HTML. SQL values are parameterized and deletion table names are allowlisted. CSV formula-like values are escaped.

Data is stored unencrypted on your computer. Back up `workspace.db` while the app is stopped. Do not commit it or private notes to GitHub. Deleting a meeting also deletes its tasks; the UI asks before deletion. Do not expose this development server on a public network; authentication, deployment hardening, migrations, and operational monitoring would be required for a hosted product.

Limits: English-focused retrieval and extraction; no PDF parsing or audio transcription; source-text character limit 30,000 per item; no semantic embeddings; no email/calendar delivery. Large datasets and concurrent multi-user operation are outside this version's scope.

## Validation

From this folder:

```bash
python -m unittest discover -s tests -v
```

12 tests passed locally, covering full support and meeting workflows, SQLite persistence, edits, cascade deletion, CSV formula escaping, invalid input, session-token checks, Host validation, traversal rejection, static routes, and model-output validation. JavaScript passed `node --check web/app.js`.

Verification limits: the remote browser preview could not reach this environment, so visual/browser interaction testing was not completed. A real Ollama model was not installed; its adapter was tested with mocked responses and missing-model failures. Offline extraction and retrieval were tested end to end over HTTP. No benchmark accuracy or production-readiness claim is made.

Built for Mahindra's portfolio with AI assistance. Extend with real user feedback and measured evaluations.

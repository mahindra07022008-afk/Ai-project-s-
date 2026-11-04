# ClientDesk — evidence-backed client support

**Problem:** Freelancers repeatedly answer questions about refunds, deliverables, and service policies, sometimes giving inconsistent answers.

**Workflow:** Save your actual policies → enter a client question → inspect matching passages → edit the reply → mark resolved. Tickets retain the source excerpts used when created, even if a policy is later removed. New drafts use the current policy library.

Run `python app.py` from the `freelancer-suite` folder and open http://127.0.0.1:8765/support.

Implemented: persistent policy library; paragraph retrieval using TF-IDF; exact evidence and similarity scores; editable reply drafts; open/resolved states; saved request search; delete controls; no-match fallback. The default response is an extractive draft and must be adapted before sending. Nothing sends email or makes decisions on your behalf.

Try the built-in demo, then replace its fictional policy with your own. Review every excerpt in context: a keyword match can include a policy exception that does not apply.

See the [suite README](../../README.md) for architecture, setup, tests, and limitations.

# ActionBoard — meeting commitments to tracked tasks

**Problem:** Action items disappear in meeting notes, with unclear ownership and missed follow-up.

**Workflow:** Paste meeting notes → extract explicit commitments → review source quotations → assign/edit owners and due dates → track todo/doing/done → export a spreadsheet.

Run `python app.py` from the `freelancer-suite` folder and open http://127.0.0.1:8765/meetings.

Implemented: persistent meeting history; offline structured-line parser; optional local Ollama integration; exact source evidence; editable task title/owner/date; progress tracking; meeting search; CSV export; deletion with cascading tasks. Missing dates remain empty; the app does not guess a calendar date from phrases such as “next Friday”.

Good offline input:

```text
Decision: Launch after final approval.
Action: Maya: Send proposal by 2026-12-15.
Arjun will review navigation.
```

Offline parsing is rule-based. For less structured notes, configure the optional local AI mode as described in the [suite README](../../README.md). Model results always require review. This version does not record audio, send reminders, or write to calendars.

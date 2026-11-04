# Validation record

- Python 3.12: 12 unit/integration tests passed.
- JavaScript: Node syntax check passed.
- Real HTTP flows exercised with isolated temporary SQLite databases.
- No user data or credentials used in tests.
- Ollama output parsing tested with mocks; live inference not tested.
- Browser preview attempted; remote browser returned ERR_CONNECTION_REFUSED. Visual interaction testing remains unverified.

Manual acceptance checklist on the user's computer:
1. Launch app.py and open the printed URL.
2. ClientDesk: fill demo, save policy, create request, verify refund evidence, edit reply and mark resolved, reload.
3. ActionBoard: fill demo, extract three tasks, edit owner/date/status, reload and confirm persistence.
4. Export CSV and inspect columns in a spreadsheet.
5. Search saved meetings and requests; inspect no-results states.
6. Test layout on a narrow window and keyboard tab navigation.
7. If a local model is configured, test actual AI extraction against manually labeled notes.

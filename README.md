# sheriff-tg-mini-app-backend

## Tests

This project uses **pytest**.

### Unit tests (default)

Unit tests do not call external services (Webflow is mocked).

Run:

- `python3 -m pytest -q`

### Integration tests (real Webflow API)

Integration tests call the real **Webflow CMS API** and are marked with `integration`.

They are **skipped by default** unless you provide:

- `WEBFLOW_CMS_ITEMS_URL`
- `WEBFLOW_API_KEY`

Run only integration tests:

- `python3 -m pytest -q -m integration`

Run everything (unit + integration):

- `python3 -m pytest -q -m "integration or not integration"`

### Notes

- If your shell does not have `pytest` on PATH, always run via `python3 -m pytest`.
- The Webflow rate fetching logic is tested in `tests/test_webflow_rates.py`.

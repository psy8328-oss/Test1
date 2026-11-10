# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Single-page Streamlit shopping list app (add / edit / delete / check items), targeted at Streamlit Community Cloud. Requirements and acceptance criteria are in `PRD.md` (section 9 = acceptance criteria the E2E tests mirror). `PROMPTS.md` holds the staged build prompts (1 skeleton → 2 features → 3 UI → 4 Playwright → 5 deploy); stages 1–4 are done. UI text and comments are Korean.

## Commands

```bash
pip install -r requirements.txt          # runtime: streamlit
pip install -r requirements-dev.txt      # pytest, pytest-playwright
playwright install chromium

streamlit run app.py                      # dev server on :8501
pytest -v                                 # all E2E tests (pytest.ini sets testpaths=tests)
pytest -k test_3_edit_item -v             # single test
pytest --headed -k test_7                 # watch the browser
```

There is no build or lint step.

## Architecture

- **`storage.py`** — JSON persistence. `DATA_FILE` defaults to `data/shopping_list.json` but is overridden by the `SHOPPING_DATA_FILE` env var (tests rely on this so real data is never touched). `save_items` writes atomically (temp file + `os.replace`); `transaction()` is a lock-guarded load→modify→save context manager.
- **`app.py`** — the whole UI. Key invariants:
  - **Items are never cached in `st.session_state`.** Every script run reads `storage.load_items()`, and every mutation goes through `with storage.transaction() as items:`. This is deliberate: multiple tabs/users share one file, and a per-session cache caused one session to overwrite another's changes (covered by `test_8`). Only UI state lives in session_state (`editing_id`, `warning`, `confirm_delete_all`, widget keys).
  - Mutations run in widget **callbacks** (`on_click`/`on_change`), not via `st.rerun()`, so the page renders once with fresh data.
  - `toggle_item` writes the checkbox's displayed value (`st.session_state[f"check_{id}"]`), not `not item["checked"]`; before rendering each checkbox its session key is set from the file so changes from other tabs show up.
  - The edit row is wrapped in `st.form` — without it, blurring the name input triggers a rerun that resets the in-progress quantity input.
  - User-entered names are passed through `md_escape()` because checkbox labels render Markdown (checked items use `:gray[~~…~~]`).
  - Widget/container keys are id-based (`row_`, `check_`, `edit_`, `del_`, `edit_name_`, `edit_qty_`, plus `add_row`, `bulk_row`). Streamlit exposes them as `.st-key-<key>` CSS classes, which both `CUSTOM_CSS` and the tests target. Renaming a key breaks styling and tests.
  - `CUSTOM_CSS` forces `flex-wrap: nowrap` on rows/add form/bulk buttons under 640px; otherwise Streamlit stacks columns vertically on mobile.
- **`tests/`** — `conftest.py` starts a dedicated Streamlit server on port **8599** with `SHOPPING_DATA_FILE` pointing at a temp file; the `app` fixture deletes that file, opens an empty page, and saves a full-page screenshot to `tests/screenshots/<test>.png` afterwards. Use `expect(...)` waits, not sleeps. After a row is removed Streamlit briefly shows the old row during rerender, so assert with `to_have_count(n)` rather than `to_be_visible()` when the list shifts. Select icon buttons with `[class*="st-key-edit_"] button:visible` (a hidden duplicate button exists in the DOM).

## Known limitations

- Streamlit Community Cloud's filesystem is ephemeral, so JSON data can be lost on app restart (PRD 7.4). No auth: anyone with the URL shares one list.
- Other sessions' changes appear only on the next interaction or reload (no live push).

## Windows shell note

When passing Korean text through a Bash heredoc to `python -` on this machine, stdin decoding garbles it. Use `\uXXXX` escapes or write a `.py` file instead. Console output of Korean may also print as `���` even when the data is correct.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Spendly** — a personal expense tracker. Server-rendered **Flask + raw `sqlite3`** monolith with Jinja2 templates. No API layer, no JS framework, no Node toolchain, no build step. Indian-locale: currency is ₹ (INR), and seed data is India-specific (Zomato, Ola, DTH recharge).

The product is named **Spendly** everywhere (DB file, templates, seed data) while the repo directory is `expense-tracker`.

This is a **teaching scaffold built in numbered steps**, not a finished product. That framing governs everything below — many things that look broken are simply not built yet.

## Architecture

Browser → Flask route → `render_template` → HTML. Entirely in-process; the browser never calls a JSON endpoint.

| Layer | Location | Notes |
|---|---|---|
| Routing | `app.py` | Single module, flat, **no Blueprints**. All routes live here. |
| Data | `database/db.py` | The entire data layer; `get_db()` is its only abstraction. |
| Views | `templates/` | `base.html` + 5 pages. |
| Assets | `static/css/`, `static/js/` | Two global stylesheets; `main.js` is empty. |
| Database | `spendly.db` (repo root, gitignored) | SQLite. |

- **No service or repository layer.** The intended shape is route → `get_db()` → raw SQL → template.
- `DB_PATH` is derived from `__file__` → `<root>/spendly.db`. **Never hardcode the DB filename** — import `get_db()`.
- Every connection sets `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. There is no Flask `g` caching and no `teardown_appcontext` — each caller opens and closes its own connection.
- **No migrations.** Schema is `CREATE TABLE IF NOT EXISTS` inside `init_db()`, so a column change means **deleting `spendly.db`** and letting startup recreate it.
- `init_db()` and `seed_db()` run at import time inside `app.app_context()` (`app.py:7-9`) — the DB is created and seeded on every boot.
- Schema: `users(id, name, email UNIQUE, password_hash, created_at)` → one-to-many → `expenses(id, user_id FK, amount REAL, category TEXT, date TEXT 'YYYY-MM-DD', description, created_at)`. `category` is bare TEXT — the fixed category list is convention only, with no CHECK constraint.
- Templates extend `base.html` (blocks `title`, `head`, `content`, `scripts`). Links use `url_for('<endpoint>')`, so the endpoint name is the contract when adding a route.
- Styling: `static/css/style.css` is the design system — `:root` tokens (`--ink*`, `--paper*`, `--accent`, `--radius-*`, `--font-display`/`--font-body`) followed by banner-comment sections. `static/css/landing.css` is a **namespaced override layer scoped to `.lp-*` only**, declaring its own palette inside `.lp-hero`. It exists because the hero was redesigned without removing the old `.hero-*` rules, so **two parallel hero styles coexist** — know which one you are editing.
- Page-specific JS is inlined in `{% block scripts %}` (e.g. the landing-page YouTube modal).

## What is developed

Done:

- **Step 1 — database layer.** `database/db.py` provides `get_db()`, `init_db()`, `seed_db()`, built to `.claude/specs/01-database-setup.md` and merged in PR #1.
- **Static pages, rendering only:** `/` (landing), `/terms`, `/privacy`.
- **Auth pages render but do not function:** `/login` and `/register` return their templates. The forms exist and include an `{% if error %}<div class="auth-error">` block.
- **Seed tooling:** `database/seed_random_user.py` and `database/seed_expenses.py`, plus matching slash commands in `.claude/commands/`.

Not built:

- **No auth at all.** `app.py` never imports `session`, `request`, or `redirect`, and `app.secret_key` is never set.
- **`login.html` and `register.html` POST to `/login` and `/register`, but both routes are GET-only — submitting either form returns HTTP 405 today.** This is expected, not a bug to hotfix; it resolves in the auth step.
- No error handlers, no 404/500 templates, no logging (`print()` only), no config module, no `.env` loading, no type hints.
- **No tests exist** despite `pytest` and `pytest-flask` being in `requirements.txt` — there is no `tests/` directory and no `conftest.py`. `db.py` computes a single module-level `DB_PATH`, so tests must monkeypatch it or they will write to the real `spendly.db`.

## Feature scope of development

Features ship as **numbered steps**, each with a spec at `.claude/specs/NN-name.md`. The placeholder routes in `app.py:45-67` name their own step in the string they return.

| Step | Scope | Route / state |
|---|---|---|
| 1 | Database setup | Done — spec `01-database-setup.md` |
| 2 | *not recorded in repo* | — |
| 3 | Logout | `/logout` — stub string |
| 4 | Profile page | `/profile` — stub string |
| 5 | *not recorded in repo* | — |
| 6 | *not recorded in repo* | — |
| 7 | Add expense | `/expenses/add` — stub string |
| 8 | Edit expense | `/expenses/<int:id>/edit` — stub string |
| 9 | Delete expense | `/expenses/<int:id>/delete` — stub string |

Steps 2, 5, and 6 have no stub route and no spec — their scope is not recorded anywhere in this repo. Do not guess at what they contain.

Working rules:

- **Read `.claude/specs/NN-*.md` before implementing a step.** Do not design from scratch, and do not fix a placeholder ad hoc.
- **Implement one step at a time.** Preserve the incremental structure; do not collapse several steps into one change.
- If a step has no spec yet, write and confirm the spec first, following the `01-` template: overview, dependencies, routes, schema, functions to implement, files to change, rules, definition of done.

## Commands

Python runs **inside Docker**, in a container named `expense-tracker-dev`.

```bash
docker build -t expense-tracker .          # the file is lowercase `dockerfile`
docker run -d --name expense-tracker-dev -p 5001:5001 expense-tracker

docker exec expense-tracker-dev python database/seed_random_user.py
docker exec expense-tracker-dev python database/seed_expenses.py <user_id> <count> <months>

docker exec expense-tracker-dev pytest tests/test_x.py::test_name   # once tests exist
```

- Serves on **port 5001** with `debug=True` (`app.py:71`).
- Demo account seeded on first boot: `demo@spendly.com` / `demo123`.
- The checked-out `venv/` was created **inside the container** (`pyvenv.cfg` → `home = /usr/local/bin`) and **does not work on the Windows host** — do not try to activate it.

## Rules

Data layer, from `.claude/specs/01-database-setup.md` §11:

- No ORM — raw `sqlite3` only.
- Parameterized queries only; never f-string, `%`, or `.format()` into SQL.
- `PRAGMA foreign_keys = ON` on every connection.
- `amount` is `REAL`; dates are `TEXT` in `YYYY-MM-DD`.
- Hash passwords with `werkzeug.security.generate_password_hash`.
- Seeds must be idempotent.
- Fixed categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other.

Conventions:

- **Errors surface via an `error` template variable, not `flash()`** — routes pass `error="..."` into the render context, and the `auth-error` markup already exists in both auth templates.
- Use the `style.css` `:root` tokens rather than raw hex values.
- Seed scripts use a `sys.path.insert(0, <root>)` bootstrap so they run from any working directory.

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this
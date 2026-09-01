# Spec: Login and Logout

## Overview
Implements session-based authentication for Spendly. `login.html` already renders a working form that POSTs to `/login`, but the route is GET-only, so submitting it returns HTTP 405 today. This step wires up `POST /login` to verify credentials against the `users` table and establish a Flask session, and implements `GET /logout` to clear that session. This is the step that turns Spendly from a set of static/registration-only pages into an app with an actual signed-in state — later steps (Profile, Add/Edit/Delete expense) depend on `session['user_id']` existing.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `users` table).
- Step 2 — Registration (`create_user`, `get_user_by_email` in `database/db.py`; existing `users` rows with `werkzeug`-hashed passwords).

## Routes
- `GET /login` — existing, unchanged — renders the login form — public
- `POST /login` — new — verifies email/password against `users`, sets `session['user_id']` and `session['user_name']` on success and redirects to `/` (landing), or re-renders `login.html` with `error` set on failure — public
- `GET /logout` — modify (currently a stub string) — clears the session and redirects to `/` — logged-in (safe to hit while logged out too; it just no-ops and redirects)

## Database changes
No database changes. The `users` table already has `password_hash`. No new column or table is needed to support login/logout.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — change the form's hardcoded `action="/login"` to `action="{{ url_for('login') }}"` (the current hardcoded path violates the project's "never hardcode URLs" rule, and register.html already does this correctly). No other markup changes — the `{% if error %}<div class="auth-error">` block is already wired up.
  - `templates/base.html` — in the shared nav (`.nav-links`), conditionally render on `session.user_id`: logged-in visitors see a `Logout` link (`url_for('logout')`) in the same top-right position the `Sign in` link occupies; logged-out visitors see `Sign in` unchanged. `Get started` (register) stays visible in both states — out of scope to hide it.
  - `templates/landing.html` — in the hero, conditionally render on `session.user_id`: logged-in visitors see a "Welcome back, `{{ session.user_name }}`" message in place of the "Create free account" / "See how it works" buttons (no duplicate Logout button here — that lives in the nav per the change above); logged-out visitors see the existing CTAs unchanged. Guard the `lp-how-it-works-btn` click handler in `{% block scripts %}` with a null check, since that button no longer renders in the logged-in branch.

## Files to change
- `app.py`:
  - Import `session` from `flask`, alongside the existing `request`, `redirect`, `url_for`.
  - Set `app.secret_key` once at module load (a hardcoded dev string is acceptable for this teaching scaffold — flag it as dev-only in a comment; do not add `.env` loading or a config module).
  - Change `/login` to accept `GET` and `POST`. On `POST`: read `email`/`password` from the form, look up the user, verify the password, and either set the session and redirect to `url_for('landing')`, or re-render `login.html` with an `error`.
  - Replace the `/logout` stub: clear the session (`session.clear()`) and `redirect(url_for('landing'))`. Remove it from the "Placeholder routes" comment block since it is no longer a stub.
- `database/db.py`:
  - Add a function to verify credentials, e.g. `verify_user(email, password)` — fetches the user by email, and if found, checks the password with `check_password_hash(user["password_hash"], password)`. Returns the user row on success, `None` on any failure (no user, wrong password). Reuse `get_user_by_email` internally rather than duplicating the query.

## Files to create
None.

## New dependencies
No new dependencies — `flask.session` and `werkzeug.security.check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug.security` — verify with `check_password_hash`, never compare `password_hash` to plaintext directly.
- Use the `style.css` CSS variables — never hardcode hex values (no new styling should be needed).
- All templates extend `base.html` (already true — no change needed here).
- Never hardcode route paths in templates — use `url_for()` (this step also fixes the existing violation in `login.html`).
- Do not add a `login_required` decorator or protect `/profile` (or any other route) in this step — route protection belongs to Step 4 (Profile page) and later steps. This step only establishes and clears the session.
- On invalid email or wrong password, re-render `login.html` with a single generic `error` message (e.g. `"Invalid email or password."`) — do not reveal whether the email exists, to avoid user enumeration.
- Do not let a missing user or `None` row raise an exception — `verify_user` must handle the "no such user" case and return `None` rather than crashing.
- On success, redirect to `url_for('landing')` — `/profile` is still a Step 4 stub, so the landing page (now session-aware) is the correct post-login destination for this step; do not fabricate a dashboard route that isn't part of this spec.
- The nav and landing page's session-aware UI must read `session` directly in the template (Flask exposes it as a Jinja global) — do not add a new route or pass extra context from `app.py` just for this.
- `GET /logout` must work even if no session exists (i.e. `session.clear()` on an already-empty session is a no-op, not an error).

## Definition of done
- `GET /login` still renders the form exactly as before, and its form now posts via `url_for('login')` instead of a hardcoded path.
- Submitting `/login` with the seeded demo account (`demo@spendly.com` / `demo123`) redirects to `/` and the response's session cookie contains the signed session data.
- After that login, the nav (on every page) shows `Logout` in place of `Sign in`, and `/` shows "Welcome back, Demo User" in the hero instead of the "Create free account" / "See how it works" CTAs.
- Visiting any page without logging in shows `Sign in` in the nav, and `/` shows the normal hero CTAs — no welcome message, no Logout link anywhere.
- Submitting `/login` with a correct email and wrong password re-renders `login.html` with an `auth-error` message and does not set any session data.
- Submitting `/login` with an email that doesn't exist re-renders `login.html` with the same generic `auth-error` message (no user enumeration) and does not set any session data.
- Visiting `/logout` after logging in clears the session (a subsequent request no longer carries `user_id`) and redirects to `/`.
- Visiting `/logout` while not logged in does not raise an error and still redirects to `/`.
- No unhandled exception/500 is raised for any of the above cases.
- `app.py` has no bare stub string return for `/logout` — it always performs the clear-and-redirect.
- All new SQL in `database/db.py` uses parameterized queries (`?` placeholders).

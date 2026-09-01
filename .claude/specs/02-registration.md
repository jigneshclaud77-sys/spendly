# Spec: Registration

## Overview
Implements account creation for Spendly. Currently `register.html` renders a working form that POSTs to `/register`, but the route is GET-only, so submitting it returns HTTP 405. This step wires up `POST /register` so a visitor can create a `users` row with a hashed password. A successful registration redirects to the `/login` page rather than establishing a session.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `users` table).

## Routes
- `GET /register` — existing, unchanged — renders the registration form — public
- `POST /register` — new — validates input, inserts the user with a hashed password, redirects to `/login` on success, or re-renders `register.html` with `error` set on failure — public

## Database changes
No database changes. The `users` table from `database/db.py` (`id`, `name`, `email UNIQUE`, `password_hash`, `created_at`) already supports this.

## Templates
- **Create:** none
- **Modify:** none — `templates/register.html` already posts `name`, `email`, `password` to `/register` and already has the `{% if error %}<div class="auth-error">` block wired up.

## Files to change
- `app.py` — import `request` and `redirect`; change `/register` to accept `GET` and `POST`; on `POST`, validate and call the new `db.py` function, then redirect or re-render with `error`.
- `database/db.py` — add a function to insert a new user (e.g. `create_user(name, email, password)`), hashing the password with `generate_password_hash` before insert.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug.security.generate_password_hash` before insert — never store plaintext.
- Use the `style.css` CSS variables — never hardcode hex values (no new styling should be needed).
- All templates extend `base.html` (already true — no change needed here).
- Do not set `app.secret_key` or touch `session` in this step — no login/session handling yet.
- Validate on the server, not just via HTML5 `required`: reject empty name/email/password and passwords under 8 characters.
- On duplicate email (`sqlite3.IntegrityError` from the `UNIQUE` constraint, or a pre-check `SELECT`), re-render `register.html` with `error="An account with that email already exists."` — do not let the exception crash the request.
- On any other validation failure, re-render `register.html` with a matching `error` message instead of raising.
- On success, `redirect(url_for('login'))` — do not fabricate a dashboard/home route that isn't part of this spec.

## Definition of done
- `GET /register` still renders the form exactly as before.
- Submitting the form with valid name/email/password ≥ 8 chars creates a new row in `users` with a `werkzeug`-hashed `password_hash` (verifiable via `check_password_hash`), and the response redirects to `/login`.
- Submitting with an email that already exists in `users` re-renders `register.html` with an `auth-error` message and does not create a duplicate row.
- Submitting with a password under 8 characters re-renders `register.html` with an `auth-error` message and does not create a row.
- No unhandled exception/500 is raised for any of the above cases.
- `app.py` has no bare stub string returns for `/register` — it always renders a template.
- All new SQL in `database/db.py` uses parameterized queries (`?` placeholders).
~
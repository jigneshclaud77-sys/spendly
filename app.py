import calendar
import sqlite3
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, session

from database.db import get_db, init_db, seed_db, get_user_by_email, create_user, verify_user
from database.queries import (
    get_user_by_id,
    get_recent_transactions,
    get_summary_stats,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = "dev-secret-key-not-for-production"  # dev-only, fine for this teaching scaffold

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="Please fill in all fields.")

    if len(password) < 8:
        return render_template(
            "register.html", error="Password must be at least 8 characters."
        )

    if get_user_by_email(email):
        return render_template(
            "register.html", error="An account with that email already exists."
        )

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template(
            "register.html", error="An account with that email already exists."
        )

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = verify_user(email, password)
    if user is None:
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _parse_iso_date(value):
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%d")


def _resolve_date_range(args):
    date_from = _parse_iso_date(args.get("date_from"))
    date_to = _parse_iso_date(args.get("date_to"))

    if not (date_from and date_to):
        return None, None, None

    if date_from > date_to:
        return None, None, "Start date must be before end date."

    return date_from, date_to, None


def _months_ago(d, months):
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _build_presets(active_date_from, active_date_to):
    today = date.today()
    preset_defs = [
        ("This Month", date(today.year, today.month, 1).isoformat(), today.isoformat()),
        ("Last 3 Months", _months_ago(today, 3).isoformat(), today.isoformat()),
        ("Last 6 Months", _months_ago(today, 6).isoformat(), today.isoformat()),
        ("All Time", None, None),
    ]
    return [
        {
            "label": label,
            "date_from": preset_from,
            "date_to": preset_to,
            "active": (preset_from, preset_to) == (active_date_from, active_date_to),
        }
        for label, preset_from, preset_to in preset_defs
    ]


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    date_from, date_to, error = _resolve_date_range(request.args)

    raw_user = get_user_by_id(user_id)
    user = {
        "name": raw_user["name"],
        "email": raw_user["email"],
        "initials": "".join(word[0] for word in raw_user["name"].split()[:2]).upper(),
        "created_at": raw_user["member_since"],
    }

    stats = get_summary_stats(user_id, date_from, date_to)
    expenses = get_recent_transactions(user_id, date_from=date_from, date_to=date_to)

    raw_categories = get_category_breakdown(user_id, date_from, date_to)
    categories = [
        {"name": c["name"], "total": c["amount"], "percent": c["pct"]}
        for c in raw_categories
    ]

    presets = _build_presets(date_from, date_to)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        expenses=expenses,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        presets=presets,
        error=error,
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session

from database.db import get_db, init_db, seed_db, get_user_by_email, create_user, verify_user

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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "created_at": "2026-01-15",
    }

    categories = [
        {"name": "Food", "total": 4200.00, "percent": 29.0},
        {"name": "Bills", "total": 3600.00, "percent": 24.8},
        {"name": "Shopping", "total": 2400.00, "percent": 16.6},
        {"name": "Transport", "total": 1850.00, "percent": 12.8},
        {"name": "Entertainment", "total": 1200.00, "percent": 8.3},
        {"name": "Health", "total": 950.00, "percent": 6.6},
        {"name": "Other", "total": 300.00, "percent": 2.1},
    ]

    stats = {
        "total_spent": sum(c["total"] for c in categories),
        "transaction_count": 24,
        "top_category": categories[0]["name"],
    }

    expenses = [
        {"date": "2026-09-02", "description": "Zomato order", "category": "Food", "amount": 450.00},
        {"date": "2026-09-01", "description": "Ola ride to airport", "category": "Transport", "amount": 620.00},
        {"date": "2026-08-29", "description": "Electricity bill (BESCOM)", "category": "Bills", "amount": 1450.00},
        {"date": "2026-08-27", "description": "BookMyShow — movie tickets", "category": "Entertainment", "amount": 600.00},
        {"date": "2026-08-25", "description": "Big Bazaar grocery run", "category": "Shopping", "amount": 1200.00},
        {"date": "2026-08-22", "description": "Apollo Pharmacy", "category": "Health", "amount": 350.00},
        {"date": "2026-08-20", "description": "DTH recharge (Tata Play)", "category": "Bills", "amount": 399.00},
    ]

    return render_template(
        "profile.html", user=user, stats=stats, expenses=expenses, categories=categories
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

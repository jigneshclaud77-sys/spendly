from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created_at.strftime("%B %Y"),
    }


def _date_filter_clause(user_id, date_from, date_to):
    where = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)
    return where, params


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    where, params = _date_filter_clause(user_id, date_from, date_to)
    params.append(limit)

    query = (
        "SELECT date, description, category, amount FROM expenses "
        + where
        + " ORDER BY date DESC, id DESC LIMIT ?"
    )

    conn = get_db()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": float(row["amount"]),
        }
        for row in rows
    ]


def get_summary_stats(user_id, date_from=None, date_to=None):
    where, params = _date_filter_clause(user_id, date_from, date_to)

    totals_query = (
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, "
        "COUNT(*) AS transaction_count FROM expenses "
        + where
    )
    top_category_query = (
        "SELECT category, SUM(amount) AS total FROM expenses "
        + where
        + " GROUP BY category ORDER BY total DESC LIMIT 1"
    )

    conn = get_db()
    try:
        totals_row = conn.execute(totals_query, params).fetchone()
        top_category_row = conn.execute(top_category_query, params).fetchone()
    finally:
        conn.close()

    top_category = top_category_row["category"] if top_category_row else "—"

    return {
        "total_spent": float(totals_row["total_spent"]),
        "transaction_count": int(totals_row["transaction_count"]),
        "top_category": top_category,
    }


def get_category_breakdown(user_id, date_from=None, date_to=None):
    where, params = _date_filter_clause(user_id, date_from, date_to)

    query = (
        "SELECT category, SUM(amount) AS total FROM expenses "
        + where
        + " GROUP BY category ORDER BY total DESC"
    )

    conn = get_db()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    overall_total = sum(row["total"] for row in rows)
    if overall_total == 0:
        return []

    breakdown = [
        {
            "name": row["category"],
            "amount": float(row["total"]),
            "pct": round(row["total"] / overall_total * 100),
        }
        for row in rows
    ]

    diff = 100 - sum(item["pct"] for item in breakdown)
    if diff != 0:
        breakdown[0]["pct"] += diff

    return breakdown

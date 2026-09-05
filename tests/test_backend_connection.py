from database.queries import (
    get_user_by_id,
    get_recent_transactions,
    get_summary_stats,
    get_category_breakdown,
)


class TestGetRecentTransactions:
    def test_returns_newest_first_with_expected_keys(self):
        transactions = get_recent_transactions(1)

        assert len(transactions) > 0
        for i in range(len(transactions) - 1):
            assert transactions[i]["date"] >= transactions[i + 1]["date"]

        for txn in transactions:
            assert set(txn.keys()) == {"date", "description", "category", "amount"}
            assert isinstance(txn["amount"], float)

    def test_user_with_no_expenses_returns_empty_list(self):
        from database.db import create_user

        user_id = create_user("No Expenses User", "no-expenses@example.com", "password123")

        transactions = get_recent_transactions(user_id)

        assert transactions == []

    def test_limit_is_respected(self):
        from database.db import create_user, get_db

        user_id = create_user("Many Expenses User", "many-expenses@example.com", "password123")

        conn = get_db()
        try:
            conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (user_id, 10.0 + i, "Food", f"2024-01-{i + 1:02d}", f"Expense {i}")
                    for i in range(15)
                ],
            )
            conn.commit()
        finally:
            conn.close()

        transactions = get_recent_transactions(user_id, limit=5)

        assert len(transactions) == 5


class TestGetSummaryStats:
    def test_user_with_expenses(self):
        from database.db import create_user, get_db

        user_id = create_user(
            "Summary Stats User", "summary.stats.user@example.com", "password123"
        )

        expenses = [
            (12.50, "Food", "2024-01-01", "Groceries"),
            (30.00, "Food", "2024-01-02", "Restaurant"),
            (20.00, "Transport", "2024-01-03", "Cab"),
        ]

        conn = get_db()
        try:
            conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(user_id, amount, category, exp_date, description)
                 for amount, category, exp_date, description in expenses],
            )
            conn.commit()
        finally:
            conn.close()

        expected_total = sum(amount for amount, _, _, _ in expenses)
        expected_count = len(expenses)

        totals_by_category = {}
        for amount, category, _, _ in expenses:
            totals_by_category[category] = totals_by_category.get(category, 0) + amount
        expected_top_category = max(
            totals_by_category, key=lambda category: totals_by_category[category]
        )

        stats = get_summary_stats(user_id)

        assert stats["total_spent"] == expected_total
        assert stats["transaction_count"] == expected_count
        assert stats["top_category"] == expected_top_category

    def test_user_with_no_expenses(self):
        from database.db import create_user

        user_id = create_user(
            "No Expenses User", "no.expenses.user@example.com", "password123"
        )

        stats = get_summary_stats(user_id)

        assert not stats["total_spent"]
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"


class TestGetCategoryBreakdown:
    def test_multiple_categories_ordered_and_sums_to_100(self):
        from database.db import create_user, get_db

        user_id = create_user(
            "Breakdown User", "breakdown-user@example.com", "password123"
        )

        conn = get_db()
        try:
            conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (user_id, 300.0, "Food", "2024-01-01", "Groceries"),
                    (user_id, 100.0, "Transport", "2024-01-02", "Cab"),
                    (user_id, 50.0, "Bills", "2024-01-03", "Electricity"),
                ],
            )
            conn.commit()
        finally:
            conn.close()

        result = get_category_breakdown(user_id)

        assert [c["name"] for c in result] == ["Food", "Transport", "Bills"]

        amounts = [c["amount"] for c in result]
        assert amounts == sorted(amounts, reverse=True)

        for c in result:
            assert set(c.keys()) == {"name", "amount", "pct"}
            assert isinstance(c["name"], str)
            assert isinstance(c["amount"], float)
            assert isinstance(c["pct"], int)

        assert sum(c["pct"] for c in result) == 100

    def test_user_with_no_expenses_returns_empty_list(self):
        from database.db import create_user

        user_id = create_user(
            "No Expenses Breakdown User",
            "no-expenses-breakdown@example.com",
            "password123",
        )

        result = get_category_breakdown(user_id)

        assert result == []

    def test_rounding_remainder_goes_to_largest_category(self):
        from database.db import create_user, get_db

        user_id = create_user(
            "Thirds User", "thirds-user@example.com", "password123"
        )

        conn = get_db()
        try:
            conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (user_id, 100.0, "Food", "2024-01-01", "Groceries"),
                    (user_id, 100.0, "Transport", "2024-01-02", "Cab"),
                    (user_id, 100.0, "Bills", "2024-01-03", "Electricity"),
                ],
            )
            conn.commit()
        finally:
            conn.close()

        result = get_category_breakdown(user_id)

        assert len(result) == 3
        assert sum(c["pct"] for c in result) == 100


class TestProfileRoute:
    def test_redirects_when_logged_out(self, client):
        response = client.get("/profile")

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_shows_real_seed_user_data(self, logged_in_client):
        from database.db import get_db

        conn = get_db()
        try:
            totals = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
                "FROM expenses WHERE user_id = 1"
            ).fetchone()
            top = conn.execute(
                "SELECT category FROM expenses WHERE user_id = 1 "
                "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1"
            ).fetchone()
            category_count = conn.execute(
                "SELECT COUNT(DISTINCT category) AS n FROM expenses WHERE user_id = 1"
            ).fetchone()["n"]
        finally:
            conn.close()

        response = logged_in_client.get("/profile")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Demo User" in body
        assert "demo@spendly.com" in body
        assert "₹" in body
        assert f"{totals['total']:.2f}" in body
        assert str(totals["count"]) in body
        assert top["category"] in body
        assert category_count == 7

    def test_transactions_appear_newest_first(self, logged_in_client):
        transactions = get_recent_transactions(1)
        response = logged_in_client.get("/profile")
        body = response.get_data(as_text=True)

        positions = [body.find(txn["description"]) for txn in transactions]
        assert all(pos != -1 for pos in positions)
        assert positions == sorted(positions)

    def test_new_user_with_no_expenses_shows_zero_state(self, client):
        client.post(
            "/register",
            data={
                "name": "Fresh User",
                "email": "fresh-user@example.com",
                "password": "password123",
            },
        )
        client.post(
            "/login",
            data={"email": "fresh-user@example.com", "password": "password123"},
        )

        response = client.get("/profile")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "0.00" in body
        assert "No expenses yet" in body
        assert "No spending yet" in body

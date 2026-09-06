"""
Tests for Step 6 - Date Filter for Profile Page.

Written strictly from `.claude/specs/06-date-filter-profile.md`. Behaviour is
verified two ways, matching the pattern already established in
`tests/test_backend_connection.py`:

  1. At the HTTP level via the test client, hitting `GET /profile` with
     query-string params the way a user clicking a preset link or submitting
     the custom-range form would.
  2. At the query-helper level (`database/queries.py`) for numeric
     correctness (totals, counts, percentages) that is awkward to assert
     reliably against rendered HTML without assuming template formatting
     details that are not specified.

DB isolation follows the convention already established in
`tests/conftest.py`: `database.db.DB_PATH` is monkeypatched to a throwaway
tempfile *before* `app` is imported, so `init_db()`/`seed_db()` (which run at
app import time) populate an isolated on-disk DB rather than the real
`spendly.db`. This test module creates its own dedicated user with
hand-placed expenses (rather than relying on the seeded demo user) so preset
date-window assertions are deterministic regardless of what day the suite is
run on.

Per the app's conventions (see CLAUDE.md), errors surface via the `error`
template variable passed into `render_template`, not via `flask.flash()`.
"""

import calendar
import uuid
from datetime import date

import pytest

from database.db import create_user, get_db
from database.queries import get_category_breakdown, get_recent_transactions, get_summary_stats


# --------------------------------------------------------------------- #
# Helpers                                                                #
# --------------------------------------------------------------------- #

def _months_before(d, months):
    """Return the date `months` calendar months before `d`.

    Mirrors the plain-English preset definitions in the spec ("This Month"
    = first day of current month; "Last 3/6 Months" = N-month window ending
    today) rather than any particular implementation.
    """
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# --------------------------------------------------------------------- #
# Fixtures                                                                #
# --------------------------------------------------------------------- #

@pytest.fixture
def filter_dates():
    today = date.today()
    return {
        "today": today,
        "this_month_start": date(today.year, today.month, 1),
        "last_month": _months_before(today, 1),
        "three_months_ago": _months_before(today, 3),
        "four_months_ago": _months_before(today, 4),
        "six_months_ago": _months_before(today, 6),
        "eight_months_ago": _months_before(today, 8),
    }


@pytest.fixture
def filter_user(filter_dates):
    """A dedicated user with four expenses spread across distinct, known
    time buckets: today, last calendar month, four months ago, and eight
    months ago. Each quick-select preset therefore captures a different,
    predictable subset regardless of what day the suite runs."""
    user_id = create_user(
        "Date Filter User", f"date-filter-user-{uuid.uuid4()}@example.com", "password123"
    )

    expenses = [
        (100.0, "Food", filter_dates["today"].isoformat(), "Today lunch"),
        (200.0, "Transport", filter_dates["last_month"].isoformat(), "Last month cab"),
        (300.0, "Bills", filter_dates["four_months_ago"].isoformat(), "Old electricity bill"),
        (400.0, "Health", filter_dates["eight_months_ago"].isoformat(), "Ancient pharmacy visit"),
    ]

    conn = get_db()
    try:
        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (user_id, amount, category, exp_date, description)
                for amount, category, exp_date, description in expenses
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return user_id


@pytest.fixture
def filter_client(client, filter_user):
    """The shared `client` fixture (see conftest.py), logged in as the
    dedicated filter_user rather than the seeded demo user."""
    with client.session_transaction() as sess:
        sess["user_id"] = filter_user
        sess["user_name"] = "Date Filter User"
    return client


ALL_DESCRIPTIONS = (
    "Today lunch",
    "Last month cab",
    "Old electricity bill",
    "Ancient pharmacy visit",
)


# --------------------------------------------------------------------- #
# Auth guard                                                              #
# --------------------------------------------------------------------- #

class TestAuthGuard:
    """Spec: no new routes are added; the existing auth guard on
    `GET /profile` must continue to apply regardless of query params."""

    def test_unauthenticated_request_redirects_to_login(self, client):
        response = client.get("/profile")

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_request_with_filter_params_still_redirects(self, client):
        response = client.get(
            "/profile?date_from=2024-01-01&date_to=2024-01-31"
        )

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        # No profile data (filtered or otherwise) should leak into the
        # redirect response body.
        assert "₹" not in response.get_data(as_text=True)


# --------------------------------------------------------------------- #
# Happy paths                                                             #
# --------------------------------------------------------------------- #

class TestUnfilteredView:
    """Spec DoD: 'Visiting /profile with no query params returns the same
    data as Step 5 (unfiltered, all expenses)' and 'The "All Time" preset
    must pass no query params (clean /profile URL)'."""

    def test_no_query_params_shows_all_expenses_unfiltered(
        self, filter_client, filter_user
    ):
        expected_stats = get_summary_stats(filter_user)

        response = filter_client.get("/profile")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert expected_stats["total_spent"] == 1000.0
        assert expected_stats["transaction_count"] == 4
        assert "₹" in body, "Expected the Rupee symbol on the profile page"
        for description in ALL_DESCRIPTIONS:
            assert description in body, f"Expected unfiltered view to include {description!r}"


class TestPresetFilters:
    """Spec DoD: each of the four quick-select presets must scope all three
    sections (summary stats, recent transactions, category breakdown) to
    its respective window."""

    def test_this_month_preset_shows_only_current_month_expenses(
        self, filter_client, filter_dates
    ):
        response = filter_client.get(
            "/profile",
            query_string={
                "date_from": filter_dates["this_month_start"].isoformat(),
                "date_to": filter_dates["today"].isoformat(),
            },
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "₹" in body
        assert "Today lunch" in body
        assert "Last month cab" not in body
        assert "Old electricity bill" not in body
        assert "Ancient pharmacy visit" not in body

    def test_last_3_months_preset_shows_expenses_in_3_month_window(
        self, filter_client, filter_dates
    ):
        response = filter_client.get(
            "/profile",
            query_string={
                "date_from": filter_dates["three_months_ago"].isoformat(),
                "date_to": filter_dates["today"].isoformat(),
            },
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Today lunch" in body
        assert "Last month cab" in body
        assert "Old electricity bill" not in body
        assert "Ancient pharmacy visit" not in body

    def test_last_6_months_preset_shows_expenses_in_6_month_window(
        self, filter_client, filter_dates
    ):
        response = filter_client.get(
            "/profile",
            query_string={
                "date_from": filter_dates["six_months_ago"].isoformat(),
                "date_to": filter_dates["today"].isoformat(),
            },
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Today lunch" in body
        assert "Last month cab" in body
        assert "Old electricity bill" in body
        assert "Ancient pharmacy visit" not in body

    def test_all_time_preset_with_no_params_shows_every_expense(
        self, filter_client
    ):
        response = filter_client.get("/profile")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        for description in ALL_DESCRIPTIONS:
            assert description in body

    def test_custom_valid_range_shows_only_expenses_within_range(
        self, filter_client, filter_dates
    ):
        last_month_iso = filter_dates["last_month"].isoformat()

        response = filter_client.get(
            "/profile",
            query_string={"date_from": last_month_iso, "date_to": last_month_iso},
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Last month cab" in body
        assert "Today lunch" not in body
        assert "Old electricity bill" not in body
        assert "Ancient pharmacy visit" not in body


# --------------------------------------------------------------------- #
# Validation                                                              #
# --------------------------------------------------------------------- #

class TestValidation:
    """Spec: 'If either parameter is absent or malformed, the route falls
    back to an "All Time" (unfiltered) view rather than erroring out.' and
    'If date_from > date_to after validation, treat both as absent (no
    filter) and [surface] a user-visible error message: "Start date must be
    before end date."' This app surfaces errors via the `error` template
    variable, not `flask.flash()` (see CLAUDE.md)."""

    def test_malformed_date_from_falls_back_to_unfiltered_view(self, filter_client):
        response = filter_client.get(
            "/profile?date_from=not-a-date&date_to=2024-01-31"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        for description in ALL_DESCRIPTIONS:
            assert description in body

    def test_malformed_date_to_falls_back_to_unfiltered_view(self, filter_client):
        response = filter_client.get(
            "/profile?date_from=2024-01-01&date_to=also-not-a-date"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        for description in ALL_DESCRIPTIONS:
            assert description in body

    def test_both_dates_malformed_does_not_error_and_falls_back(self, filter_client):
        response = filter_client.get(
            "/profile?date_from=banana&date_to=xyz123"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        for description in ALL_DESCRIPTIONS:
            assert description in body

    @pytest.mark.parametrize(
        "date_from,date_to",
        [
            ("2024-13-40", "2024-01-31"),
            ("not-a-date", "not-a-date-either"),
            ("2024/01/01", "2024/01/31"),
        ],
    )
    def test_malformed_dates_never_return_a_server_error(
        self, filter_client, date_from, date_to
    ):
        response = filter_client.get(
            "/profile", query_string={"date_from": date_from, "date_to": date_to}
        )

        assert response.status_code == 200

    def test_date_from_after_date_to_shows_error_and_falls_back_to_unfiltered(
        self, filter_client, filter_dates
    ):
        response = filter_client.get(
            "/profile",
            query_string={
                "date_from": filter_dates["today"].isoformat(),
                "date_to": filter_dates["last_month"].isoformat(),
            },
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Start date must be before end date." in body
        for description in ALL_DESCRIPTIONS:
            assert description in body, (
                "date_from > date_to must fall back to the unfiltered view"
            )


# --------------------------------------------------------------------- #
# DB side effects / correctness                                          #
# --------------------------------------------------------------------- #

class TestCategoryBreakdownCorrectness:
    """Spec: 'percentage recalculation logic remains unchanged' for
    `get_category_breakdown` when a date range is supplied."""

    def test_percentages_sum_to_100_for_a_filtered_range(
        self, filter_user, filter_dates
    ):
        result = get_category_breakdown(
            filter_user,
            date_from=filter_dates["three_months_ago"].isoformat(),
            date_to=filter_dates["today"].isoformat(),
        )

        assert len(result) == 2, "Expected Food and Transport in the last-3-months window"
        assert sum(c["pct"] for c in result) == 100

    def test_percentages_sum_to_100_for_the_full_unfiltered_range(self, filter_user):
        result = get_category_breakdown(filter_user)

        assert len(result) == 4
        assert sum(c["pct"] for c in result) == 100


class TestZeroMatchDateRange:
    """Spec DoD: 'A user with no expenses in the selected range sees ₹0.00
    total spent, 0 transactions, and an empty category breakdown — no
    errors.'"""

    def test_query_helpers_return_zero_state_for_empty_range(self, filter_user):
        stats = get_summary_stats(
            filter_user, date_from="2000-01-01", date_to="2000-01-31"
        )
        transactions = get_recent_transactions(
            filter_user, date_from="2000-01-01", date_to="2000-01-31"
        )
        breakdown = get_category_breakdown(
            filter_user, date_from="2000-01-01", date_to="2000-01-31"
        )

        assert stats["total_spent"] == 0
        assert stats["transaction_count"] == 0
        assert transactions == []
        assert breakdown == []

    def test_profile_page_renders_zero_state_without_error_for_empty_range(
        self, filter_client
    ):
        response = filter_client.get(
            "/profile?date_from=2000-01-01&date_to=2000-01-31"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "0.00" in body
        for description in ALL_DESCRIPTIONS:
            assert description not in body

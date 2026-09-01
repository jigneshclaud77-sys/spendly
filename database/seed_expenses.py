import argparse
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db

CATEGORIES = [
    ("Food", 50, 800, 0.30, [
        "Groceries", "Lunch with colleagues", "Zomato order", "Swiggy order",
        "Tiffin service", "Street food", "Dinner at restaurant", "Tea and snacks",
    ]),
    ("Transport", 20, 500, 0.20, [
        "Auto rickshaw fare", "Ola ride", "Uber ride", "Metro card recharge",
        "Bus pass top-up", "Petrol", "Parking fee", "Train ticket",
    ]),
    ("Bills", 200, 3000, 0.15, [
        "Electricity bill", "Mobile recharge", "Internet bill", "Gas cylinder",
        "Water bill", "DTH recharge", "Maintenance charges",
    ]),
    ("Shopping", 200, 5000, 0.15, [
        "New shoes", "Clothes shopping", "Amazon order", "Flipkart order",
        "Home decor", "Electronics accessory", "Gift purchase",
    ]),
    ("Other", 50, 1000, 0.10, [
        "Miscellaneous", "Donation", "Stationery", "Courier charges",
        "ATM withdrawal fee", "Pet supplies",
    ]),
    ("Entertainment", 100, 1500, 0.05, [
        "Movie night", "Netflix subscription", "Concert tickets",
        "Gaming purchase", "Amusement park", "Bowling",
    ]),
    ("Health", 100, 2000, 0.05, [
        "Pharmacy", "Doctor consultation", "Gym membership", "Lab tests",
        "Health supplements", "Dental checkup",
    ]),
]

WEIGHTS = [c[3] for c in CATEGORIES]


def random_date(months):
    end = datetime.now()
    start = end - timedelta(days=months * 30)
    delta_days = (end - start).days
    offset = random.randint(0, max(delta_days, 0))
    return start + timedelta(days=offset)


def generate_expense(months):
    category, low, high, _, descriptions = random.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
    amount = round(random.uniform(low, high), 2)
    description = random.choice(descriptions)
    exp_date = random_date(months).strftime("%Y-%m-%d")
    return amount, category, exp_date, description


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("user_id", type=int)
    parser.add_argument("count", type=int)
    parser.add_argument("months", type=int)

    try:
        args = parser.parse_args()
    except (SystemExit, ValueError):
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        return

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?", (args.user_id,)
        ).fetchone()
        if not user:
            print(f"No user found with id {args.user_id}.")
            return

        expenses = [generate_expense(args.months) for _ in range(args.count)]

        conn.execute("BEGIN")
        try:
            cursor = conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(args.user_id, amount, category, exp_date, description)
                 for amount, category, exp_date, description in expenses],
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        dates = sorted(exp[2] for exp in expenses)
        sample = conn.execute(
            """
            SELECT id, amount, category, date, description
            FROM expenses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (args.user_id, min(5, args.count)),
        ).fetchall()

        print(f"Inserted {len(expenses)} expenses for user_id {args.user_id}.")
        print(f"Date range: {dates[0]} to {dates[-1]}")
        print("Sample of inserted records:")
        for row in sample:
            print(
                f"  id={row['id']} amount=₹{row['amount']:.2f} "
                f"category={row['category']} date={row['date']} "
                f"description={row['description']}"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

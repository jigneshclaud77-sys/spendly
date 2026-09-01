import os
import random
import sys
from datetime import datetime

from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohan", "Divya",
    "Karthik", "Meera", "Suresh", "Kavya", "Arjun", "Pooja", "Sanjay", "Neha",
    "Vijay", "Anjali", "Rajesh", "Shreya", "Manish", "Ritu", "Deepak", "Swati",
    "Nikhil", "Isha", "Aditya", "Preeti", "Ganesh", "Lakshmi", "Harish", "Radha",
    "Varun", "Nandini", "Siddharth", "Kirti", "Vivek", "Bhavna", "Naveen", "Sunita",
]

LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Nair", "Reddy", "Gupta", "Menon", "Patel",
    "Rao", "Singh", "Kulkarni", "Joshi", "Chatterjee", "Bhat", "Desai", "Pillai",
    "Mukherjee", "Agarwal", "Chauhan", "Naidu", "Krishnan", "Bose", "Kapoor", "Trivedi",
    "Shetty", "Malhotra", "Banerjee", "Choudhury", "Rathore", "Bansal",
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com"]


def generate_user():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    suffix = random.randint(10, 999)
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{first.lower()}.{last.lower()}{suffix}@{domain}"
    return name, email


def main():
    conn = get_db()
    try:
        name, email = generate_user()
        while conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone():
            name, email = generate_user()

        password_hash = generate_password_hash("password123")
        created_at = datetime.now().isoformat(sep=" ", timespec="seconds")

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, created_at),
        )
        conn.commit()
        user_id = cursor.lastrowid

        print("Seeded user:")
        print(f"  id:    {user_id}")
        print(f"  name:  {name}")
        print(f"  email: {email}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

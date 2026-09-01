"""Seeded synthetic data: a realistic West/East African fintech customer base.

No proprietary data, everything here is generated.
The generator deliberately injects dirty rows (null ids, negative amounts,
failed transactions) so the staging layer has real cleaning work to do.
"""

from __future__ import annotations

import argparse
import csv
import random
import tempfile
from datetime import date, timedelta
from pathlib import Path

import duckdb

SEED = 42
N_CUSTOMERS = 5_000
DIRTY_ROW_RATE = 0.02

COUNTRIES = {
    "SN": ("XOF", 0.30), "CI": ("XOF", 0.20), "BJ": ("XOF", 0.10),
    "NG": ("NGN", 0.25), "KE": ("KES", 0.15),
}
SEGMENTS = {"nano": (0.55, 30, 150), "micro": (0.35, 120, 600), "sme": (0.10, 500, 3000)}
CATEGORIES = ["airtime", "groceries", "transport", "utilities", "school_fees",
              "health", "merchant_pos", "p2p_transfer", "savings", "loan_repayment"]
CHANNELS = [("mobile", 0.72), ("pos", 0.14), ("web", 0.08), ("atm", 0.06)]
MERCHANTS = ["Wave", "Orange Money", "MTN MoMo", "Auchan", "Total", "Carrefour",
             "Sonatel", "M-Pesa Agent", "Jumia", "Local Market"]

FX_TO_USD = {"XOF": 655.957, "NGN": 1550.0, "KES": 130.0}


def _weighted(rng: random.Random, weights_by_key: dict[str, float]) -> str:
    keys = list(weights_by_key)
    return rng.choices(keys, weights=[weights_by_key[k] for k in keys])[0]


COUNTRY_WEIGHTS = {code: share for code, (_, share) in COUNTRIES.items()}
SEGMENT_WEIGHTS = {name: share for name, (share, _, _) in SEGMENTS.items()}


def generate_customers(rng: random.Random) -> list[tuple]:
    today = date.today()
    rows = []
    for i in range(N_CUSTOMERS):
        segment = _weighted(rng, SEGMENT_WEIGHTS)
        _, lo, hi = SEGMENTS[segment]
        country = _weighted(rng, COUNTRY_WEIGHTS)
        registered = today - timedelta(days=rng.randint(30, 2000))
        # thin-file customers: ~40% have no bureau score at all
        bureau = rng.randint(300, 850) if rng.random() > 0.40 else None
        rows.append((
            f"C{i:06d}",
            registered.isoformat(),
            rng.randint(18, 65),
            rng.choice(["F", "M"]),
            country,
            segment,
            round(rng.uniform(lo, hi), 2),
            rng.random() < 0.85,
            rng.random() < 0.35,
            bureau,
        ))
    return rows


def generate_transactions(rng: random.Random, customers: list[tuple]) -> list[tuple]:
    today = date.today()
    rows = []
    tx_id = 0
    for customer in customers:
        customer_id, _, _, _, country, segment, income = customer[:7]
        currency = COUNTRIES[country][0]
        # ~6% of customers are dormant: registered but never transacted
        if rng.random() < 0.06:
            continue
        monthly_tx = {"nano": 12, "micro": 25, "sme": 45}[segment]
        n_tx = max(1, int(rng.gauss(monthly_tx * 3, monthly_tx)))
        for _ in range(n_tx):
            tx_id += 1
            tx_date = today - timedelta(days=min(89, int(abs(rng.gauss(0, 35)))))
            local_amount = round(
                max(0.5, rng.lognormvariate(0, 1.0) * income * 0.02) * FX_TO_USD[currency], 2
            )
            dirty = rng.random() < DIRTY_ROW_RATE
            rows.append((
                f"T{tx_id:08d}",
                None if dirty and rng.random() < 0.3 else customer_id,
                tx_date.isoformat(),
                -local_amount if dirty and rng.random() < 0.3 else local_amount,
                currency,
                rng.choice(CATEGORIES),
                "debit" if rng.random() < 0.78 else "credit",
                _weighted(rng, dict(CHANNELS)),
                rng.random() < 0.03,
                "failed" if dirty else rng.choices(
                    ["completed", "reversed"], weights=[0.985, 0.015]
                )[0],
                rng.choice(MERCHANTS),
            ))
    return rows


def load(db_path: str) -> tuple[int, int]:
    rng = random.Random(SEED)
    customers = generate_customers(rng)
    transactions = generate_transactions(rng, customers)

    con = duckdb.connect(db_path)
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("DROP TABLE IF EXISTS raw.customers")
        con.execute("DROP TABLE IF EXISTS raw.transactions")
        con.execute("""
            CREATE TABLE raw.customers (
                customer_id VARCHAR, registration_date DATE, age INTEGER,
                gender VARCHAR, country VARCHAR, segment VARCHAR,
                monthly_income DOUBLE, has_mobile_money BOOLEAN,
                has_bank_account BOOLEAN, credit_bureau_score INTEGER
            )
        """)
        con.execute("""
            CREATE TABLE raw.transactions (
                transaction_id VARCHAR, customer_id VARCHAR, transaction_date DATE,
                amount DOUBLE, currency VARCHAR, merchant_category VARCHAR,
                transaction_type VARCHAR, channel VARCHAR,
                is_international BOOLEAN, status VARCHAR, merchant_name VARCHAR
            )
        """)
        # COPY from CSV: row-by-row executemany takes minutes for ~380k rows
        with tempfile.TemporaryDirectory() as tmp:
            for name, rows in (("customers", customers), ("transactions", transactions)):
                csv_path = Path(tmp) / f"{name}.csv"
                with open(csv_path, "w", newline="") as handle:
                    csv.writer(handle).writerows(rows)
                con.execute(f"COPY raw.{name} FROM '{csv_path}' (FORMAT CSV, NULL '')")
    finally:
        con.close()
    return len(customers), len(transactions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="scoring.duckdb")
    args = parser.parse_args()
    n_customers, n_tx = load(args.db)
    print(f"{n_customers} customers, {n_tx} transactions -> {args.db}")

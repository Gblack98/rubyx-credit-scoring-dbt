import random

from data_generator.generate import (
    DIRTY_ROW_RATE,
    SEED,
    generate_customers,
    generate_transactions,
)


def dataset():
    rng = random.Random(SEED)
    customers = generate_customers(rng)
    return customers, generate_transactions(rng, customers)


def test_deterministic_with_seed():
    assert dataset() == dataset()


def test_customer_shape():
    customers, _ = dataset()
    assert len(customers) == 5_000
    ids = [c[0] for c in customers]
    assert len(set(ids)) == len(ids)
    # thin-file customers exist (bureau_score is None)
    assert any(c[9] is None for c in customers)


def test_transactions_reference_known_customers():
    customers, transactions = dataset()
    known = {c[0] for c in customers}
    unknown = [t for t in transactions if t[1] is not None and t[1] not in known]
    assert unknown == []


def test_dirty_rows_are_present_but_flagged_failed():
    _, transactions = dataset()
    dirty = [t for t in transactions if t[1] is None or t[3] <= 0]
    assert dirty, "generator must inject dirty rows for staging to clean"
    assert all(t[9] == "failed" for t in dirty)
    assert len(dirty) / len(transactions) < DIRTY_ROW_RATE * 2


def test_some_customers_are_dormant():
    customers, transactions = dataset()
    active = {t[1] for t in transactions}
    dormant = {c[0] for c in customers} - active
    assert len(dormant) > 100  # left-join path in credit_features is exercised

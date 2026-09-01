# credit-scoring-dbt

Credit scoring feature engineering with dbt: raw fintech transactions (mobile money, POS, transfers across West/East Africa) → ML-ready feature table, one row per customer.

```
raw.customers / raw.transactions   (seeded synthetic generator, dirty rows included)
    ↓ staging      clean, filter failed/reversed, normalize XOF/NGN/KES → USD
    ↓ marts        credit_features: RFM, velocity, behavioral ratios, income burden
    → scoring model (LightGBM & co)
```

Data is synthetic, produced by the seeded generator in `data_generator/`: realistic distributions, thin-file customers with no bureau score, dormant accounts, and about 2% of dirty rows so the staging layer has something to do. No proprietary data.

## Run

```bash
pip install dbt-duckdb pytest
python data_generator/generate.py --db scoring.duckdb   # 5,000 customers, ~380k transactions
export SCORING_DB_PATH=$PWD/scoring.duckdb
dbt build --project-dir . --profiles-dir .
pytest
```

Feature highlights: `days_since_last_tx`, `tx_count_30d/7d/24h`, `mobile_tx_ratio`, `intl_tx_ratio`, `monthly_spend_to_income_ratio`, amount velocity. Guardrails: dbt tests on uniqueness/relationships plus singular tests (ratios bounded to [0,1], full customer coverage, since a scoring batch that silently drops customers is an incident).

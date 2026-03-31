# 🏗️ Credit Scoring Feature Engineering with dbt

![dbt](https://img.shields.io/badge/dbt-1.7-orange) ![SQL](https://img.shields.io/badge/SQL-PostgreSQL-blue) ![Fintech](https://img.shields.io/badge/Domain-Fintech-green) ![Africa](https://img.shields.io/badge/Market-Africa-red)

> dbt project that transforms raw transaction data into ML-ready credit features — inspired by platforms like **Rubyx.io** (scoring 8.4M+ customers daily in Africa).

## Architecture

```
Raw Data (transactions, customers, mobile money)
    ↓
[staging/] — clean, standardize, normalize currencies (XOF, NGN, KES → USD)
    ↓
[intermediate/] — ephemeral aggregations (RFM, velocity, behavioral)
    ↓
[marts/credit_features] — final ML feature table (materialized)
    ↓
ML Model (LightGBM / XGBoost) → Credit Score (300-850) + Risk Band (A/B/C/D)
```

## dbt Models

| Model | Layer | Description |
|-------|-------|-------------|
| `stg_transactions` | staging | Clean transactions, normalize currencies |
| `stg_customers` | staging | Customer profiles (age, income, segment) |
| `credit_features` | marts | **Master feature table** for ML scoring |

## Key Features Computed

| Feature | Business Signal |
|---------|----------------|
| `tx_count_30d` | Recent activity |
| `mobile_tx_ratio` | Mobile-first behavior (key in Africa) |
| `monthly_spend_to_income_ratio` | Debt burden proxy |
| `days_since_last_tx` | Recency signal |
| `intl_tx_ratio` | International exposure |
| `amount_24h_usd` | Velocity (fraud/risk signal) |

## Setup

```bash
pip install dbt-postgres
dbt deps
dbt run --select marts.credit_features
dbt test
```

## Profiles (profiles.yml)

```yaml
rubyx:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST') }}"
      user: "{{ env_var('DB_USER') }}"
      password: "{{ env_var('DB_PASSWORD') }}"
      dbname: rubyx_dev
      schema: dbt_dev
```

## Inspired By

This project is inspired by the data engineering challenges at **[Rubyx.io](https://www.rubyx.io)** — a digital lending platform operating across 13+ African countries with 8.4M+ customers scored daily.

## Author

**Ibrahima Gabar Diop** — [GitHub](https://github.com/Gblack98) · [Kaggle](https://www.kaggle.com/ibrahimagabardiop)

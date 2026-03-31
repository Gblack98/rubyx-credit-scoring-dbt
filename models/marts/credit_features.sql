-- credit_features.sql
-- Feature store mart: all ML-ready credit features per customer
-- Consumed directly by the credit scoring model

with customers as (
    select * from {{ ref('stg_customers') }}
),

transactions as (
    select * from {{ ref('stg_transactions') }}
),

-- RFM + behavioral features
tx_features as (
    select
        customer_id,

        -- Recency
        date_part('day', current_date - max(transaction_date))  as days_since_last_tx,

        -- Frequency
        count(*)                                                 as total_tx_count,
        count(*) filter (where transaction_date >= current_date - 30)
                                                                 as tx_count_30d,
        count(*) filter (where transaction_date >= current_date - 7)
                                                                 as tx_count_7d,

        -- Monetary
        sum(amount_usd)                                         as total_amount_usd,
        avg(amount_usd)                                         as avg_tx_amount_usd,
        stddev(amount_usd)                                      as std_tx_amount_usd,
        max(amount_usd)                                         as max_tx_amount_usd,
        sum(amount_usd) filter (where transaction_date >= current_date - 30)
                                                                 as total_amount_30d_usd,

        -- Behavioral
        count(distinct merchant_category)                        as unique_categories,
        count(*) filter (where channel = 'mobile')
          * 1.0 / nullif(count(*), 0)                           as mobile_tx_ratio,
        count(*) filter (where is_international)
          * 1.0 / nullif(count(*), 0)                           as intl_tx_ratio,
        count(*) filter (where transaction_type = 'debit')
          * 1.0 / nullif(count(*), 0)                           as debit_ratio,

        -- Velocity (risk signal)
        count(*) filter (
            where transaction_date >= current_date - 1
        )                                                        as tx_count_24h,
        sum(amount_usd) filter (
            where transaction_date >= current_date - 1
        )                                                        as amount_24h_usd

    from transactions
    group by customer_id
),

final as (
    select
        c.customer_id,
        c.age,
        c.gender,
        c.country_code,
        c.segment,
        c.monthly_income_usd,
        c.has_mobile_money,
        c.has_bank_account,
        c.bureau_score,
        c.days_since_registration,

        -- Transaction features
        coalesce(t.days_since_last_tx, 999)         as days_since_last_tx,
        coalesce(t.total_tx_count, 0)               as total_tx_count,
        coalesce(t.tx_count_30d, 0)                 as tx_count_30d,
        coalesce(t.tx_count_7d, 0)                  as tx_count_7d,
        coalesce(t.total_amount_usd, 0)             as total_amount_usd,
        coalesce(t.avg_tx_amount_usd, 0)            as avg_tx_amount_usd,
        coalesce(t.std_tx_amount_usd, 0)            as std_tx_amount_usd,
        coalesce(t.max_tx_amount_usd, 0)            as max_tx_amount_usd,
        coalesce(t.total_amount_30d_usd, 0)         as total_amount_30d_usd,
        coalesce(t.unique_categories, 0)            as unique_categories,
        coalesce(t.mobile_tx_ratio, 0)              as mobile_tx_ratio,
        coalesce(t.intl_tx_ratio, 0)                as intl_tx_ratio,
        coalesce(t.debit_ratio, 0)                  as debit_ratio,
        coalesce(t.tx_count_24h, 0)                 as tx_count_24h,
        coalesce(t.amount_24h_usd, 0)               as amount_24h_usd,

        -- Derived ratios (key credit signals)
        case
            when c.monthly_income_usd > 0
            then coalesce(t.total_amount_30d_usd, 0) / c.monthly_income_usd
            else null
        end                                         as monthly_spend_to_income_ratio,

        current_timestamp                           as features_computed_at

    from customers c
    left join tx_features t using (customer_id)
)

select * from final

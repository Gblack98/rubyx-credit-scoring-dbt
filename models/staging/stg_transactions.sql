-- stg_transactions.sql
-- Staging layer: clean and standardize raw transaction data

with source as (
    select * from {{ source('raw', 'transactions') }}
),

cleaned as (
    select
        transaction_id::varchar                         as transaction_id,
        customer_id::varchar                            as customer_id,
        cast(transaction_date as timestamp)             as transaction_at,
        date_trunc('day', transaction_date)             as transaction_date,
        amount::numeric(18, 2)                          as amount,
        currency::varchar(3)                            as currency,
        -- Normalize to USD (simplified — use exchange rate table in production)
        case
            when currency = 'XOF' then amount / 655.957   -- CFA Franc
            when currency = 'NGN' then amount / 1550.0    -- Nigerian Naira
            when currency = 'KES' then amount / 130.0     -- Kenyan Shilling
            else amount
        end                                             as amount_usd,
        merchant_category::varchar                      as merchant_category,
        transaction_type::varchar                       as transaction_type,
        channel::varchar                                as channel,  -- mobile, web, pos, atm
        is_international::boolean                       as is_international,
        status::varchar                                 as status,  -- completed, failed, reversed
        lower(trim(merchant_name))                      as merchant_name
    from source
    where transaction_id is not null
      and amount > 0
      and status = 'completed'
)

select * from cleaned

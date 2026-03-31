-- stg_customers.sql
with source as (
    select * from {{ source('raw', 'customers') }}
),
cleaned as (
    select
        customer_id::varchar                            as customer_id,
        cast(registration_date as timestamp)            as registered_at,
        age::integer                                    as age,
        gender::varchar(1)                              as gender,
        country::varchar(2)                             as country_code,
        segment::varchar                                as segment,  -- nano, micro, sme
        monthly_income::numeric(18,2)                   as monthly_income_usd,
        has_mobile_money::boolean                       as has_mobile_money,
        has_bank_account::boolean                       as has_bank_account,
        credit_bureau_score::integer                    as bureau_score,
        -- Derived
        date_part('day', current_date - registration_date) as days_since_registration
    from source
    where customer_id is not null
)
select * from cleaned

-- Ratio features feed the scoring model directly: out-of-range values mean
-- a broken aggregation, and the model would silently learn garbage.

select customer_id, mobile_tx_ratio, intl_tx_ratio, debit_ratio
from {{ ref('credit_features') }}
where mobile_tx_ratio not between 0 and 1
   or intl_tx_ratio not between 0 and 1
   or debit_ratio not between 0 and 1

-- The feature table must cover the whole customer base: a scoring batch
-- that silently drops customers is a production incident, not a detail.

select c.customer_id
from {{ ref('stg_customers') }} c
left join {{ ref('credit_features') }} f using (customer_id)
where f.customer_id is null

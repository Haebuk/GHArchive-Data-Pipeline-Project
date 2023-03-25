{{
    config(
        materialized='incremental',
        unique_key=['dt', 'type']
    )
}}
select
    date_trunc(created_at, hour) as dt,
    type,
    count(*) as count
from {{ ref('stg_gh_events') }}
{% if is_incremental() %}

    where created_at >= (select max(dt) from {{ this }})

{% endif %}
group by dt, type
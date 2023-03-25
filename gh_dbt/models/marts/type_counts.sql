{{
    config(
        materialized='incremental',
        unique_key=['date', 'type']
    )
}}
select
    format_date('%Y-%m-%d', date_trunc(created_at, day)) as date,
    type,
    count(*) as count
from {{ ref('stg_gh_events') }}
{% if is_incremental() %}

    where created_at >= (select max(created_at) from {{ this }})

{% endif %}
group by date, type
order by date desc, count desc
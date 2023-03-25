{{
    config(
        materialized='incremental',
        unique_key=['dt', 'repo_name'],
        partition_by={
            'field': 'dt',
            'data_type': 'timestamp', 
            'granularity': 'day'
        },
        incremental_strategy='insert_overwrite'
    )
}}

select
    date_trunc(created_at, hour) as dt,
    repo_name,
    count(*) as count
from {{ ref('stg_gh_events') }}
{% if is_incremental() %}

    where created_at >= (select max(dt) from {{ this }})

{% endif %}
group by dt, repo_name
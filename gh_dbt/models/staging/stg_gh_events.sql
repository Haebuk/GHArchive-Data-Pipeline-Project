{{
    config(
        materialized='incremental',
        unique_key='id'
    )
}}

with raw as 
(
    select
        id,
        type,
        actor.login as actor_login,
        repo.name as repo_name,
        repo.url as repo_url,
        created_at,
        year,
        month,
        day
    from {{ source('github_dataset', 'gharchive') }}

    {% if is_incremental() %}

        where year >= (select max(year) from {{ this }})
        and month >= (select max(month) from {{ this }})
        and day >= (select max(day) from {{ this }})

    {% endif %}
)

{{ dbt_utils.deduplicate(
    relation='raw',
    partition_by='id',
    order_by='created_at desc',
   )
}}
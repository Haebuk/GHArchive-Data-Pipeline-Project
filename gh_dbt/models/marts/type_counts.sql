select
    type,
    count(*) as count
from {{ ref('stg_gh_events') }}
group by type
order by count
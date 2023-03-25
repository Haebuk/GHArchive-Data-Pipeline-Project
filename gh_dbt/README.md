# Github Archive DBT Project

If you're more comfortable with Korean, see [here](./README-KR.md).


## Initialization
Set up a virtual environment for DBT development and download the package.
```
$ virtualenv venv-dbt --python=python3.10
$ source venv-dbt/bin/activate
(venv-dbt)$ pip install -r requirements-dbt.txt
```

Create a DBT project.
```
# dbt init
```

In this project, I configured the `staging` layer and the `marts` layer. I referenced the [official documentation](https://docs.getdbt.com/guides/best-practices/how-we-structure/1-guide-overview) for the DBT project structure.

```yaml
# dbt_project.yml
gh_dbt:
staging:
    +materialized: view
marts:
    +materialized: table
```

I configured the `staging` layer to be created as a `view table` by default, and the `marts` layer to be created as a `table`. (In practice, due to the large size of the data, I used `incremetal` materialization to keep costs down).

## Staging Layer
```
staging
 ┣ _gh_archive__models.yml
 ┣ _gh_archive__sources.yml
 ┗ stg_gh_events.sql
```
The model inside the `staging` layer is the only place that looks at the original source (raw data). 
The YML files that make up the model and the source have `_` in front of the filenames to make them more readable.

Since the model runs once every day, I used incremental refinement so that the model only get the days it runs.

```sql
-- stg_gh_events.sql
{{
    config(
        materialized='incremental',
        unique_key='id',
        partition_by={
        "field": "created_at",
        "data_type": "timestamp",
        "granularity": "day"
        },
        incremental_strategy='insert_overwrite'
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

```

I also selected only the fields I wanted to use for the `marts` model from the `actor` and `repo` struct fields.

I noticed that there were duplicate records in the data (records with the same `id`). (I felt the greatness of DBT Test.) To remove them, I used the `dbt_utils.deduplicate` macro.

To use the `dbt_utils` package, you need to specify the package in [packages.yml] (packages.yml) and run the `dbt deps` command.


## Marts Layer
```
marts
 ┣ _marts__models.yml
 ┣ repo_counts.sql
 ┗ type_counts.sql
```

The model in the `marts` layer references the model in the `staging` layer. 
The `marts` model is the model that is aggregated from the `staging` model. 

Here, I have two models that aggregate the type and repository of the events that occurred at each hour.

I imported these two models from looker to create a dashboard.

## Deployment
Deployment was done by making the corresponding Github repository visible to DBT Cloud, and then creating a job in DBT Cloud. 

Since I don't have many models, I configured it to run via the `dbt build` command.

I configured it to send an email notification if a model fails to run.

<img width="1440" alt="image" src="https://user-images.githubusercontent.com/68543150/227726801-5d7a9261-88f6-4342-bf3c-77c5c4b92911.png">

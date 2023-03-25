# Github Archive DBT Project

영어가 친숙하다면 [여기](./README.md)를 참조하세요.


## Initialization
DBT 개발을 위한 가상환경 설정을 하고 패키지를 다운 받습니다.
```
$ virtualenv venv-dbt --python=python3.10
$ source venv-dbt/bin/activate
(venv-dbt)$ pip install -r requirements-dbt.txt
```

DBT 프로젝트를 생성합니다.
```
# dbt init
```

이번 프로젝트에서는 `staging` 레이어와 `marts` 레이어를 구성했습니다. DBT 프로젝트 구조는 [공식 문서](https://docs.getdbt.com/guides/best-practices/how-we-structure/1-guide-overview)를 참조했습니다.

```yaml
# dbt_project.yml
gh_dbt:
staging:
    +materialized: view
marts:
    +materialized: table
```

`staging` 레이어는 기본적으로 view table로 생성되게, `marts`레이어는 table로 생성되게 구성했습니다. (실제로는 데이터의 크기가 크기 때문에 비용을 절감하고자 incremetal materialization을 사용했습니다.)

## Staging Layer
```
staging
 ┣ _gh_archive__models.yml
 ┣ _gh_archive__sources.yml
 ┗ stg_gh_events.sql
```
`staging` 레이어 내 모델은 원천 소스 (raw data)를 바라보는 유일한 곳입니다. 
모델과 소스를 구성하는 yml 파일은 파일명 앞에 `_`를 붙여 가독성을 높였습니다.

모델이 매일 한 번씩 실행되므로, 실행되는 날짜만 받아올 수 있도록 증분 구체화를 사용했습니다.

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

또한 `actor`와 `repo` struct 필드에서 `marts` 모델에 사용할 필드만 선택하였습니다.

데이터 내에 중복된 레코드(같은 `id`를 가지는 레코드가 존재)가 있는 것을 확인했습니다. (DBT Test의 위대함을 느꼈습니다.) 이를 제거하기 위해 `dbt_utils.deduplicate` macro를 사용했습니다.

`dbt_utils` 패키지를 사용하려면 [packages.yml](packages.yml)에 패키지를 명시하고 `dbt deps` 명령어를 실행해야 합니다.

## Marts Layer
```
marts
 ┣ _marts__models.yml
 ┣ repo_counts.sql
 ┗ type_counts.sql
```

`marts` 레이어의 모델은 `staging` 레이어의 모델을 참고합니다. `marts`모델은 `staging` 모델에서 집계가 이루어진 모델입니다. 

여기서는 각 시간 마다 발생한 이벤트의 type과 repository를 집계한 두 모델이 있습니다.

이 두 모델을 looker에서 임포트해서 대시보드를 만들었습니다.

## Deployment
배포는 해당 Github 레포지토리를 DBT Cloud에서 바라보도록 만든 후, DBT Cloud에서 Job을 만들어 수행했습니다. 

모델이 많지 않기 때문에 `dbt build` 명령어를 통해 실행되도록 구성했습니다.

모델 실행이 실패하면 이메일로 알림을 발송하도록 구성했습니다.

<img width="1440" alt="image" src="https://user-images.githubusercontent.com/68543150/227726801-5d7a9261-88f6-4342-bf3c-77c5c4b92911.png">

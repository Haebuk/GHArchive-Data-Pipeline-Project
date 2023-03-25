# Github Archive Data Pipeline Project

영어가 친숙하다면 [여기](readme.md)를 참조하세요.

깃허브에서는 실제로 어떤 이벤트가 많이 발생할까요? 가장 많은 이벤트가 발생하는 레포지토리는 어디일까요? 이번 프로젝트를 통해 깃허브에서 가장 많이 발생하는 이벤트는 '푸시' 이벤트이며, 3월 가장 많은 이벤트가 발생한 곳은 [Lombiq/Orchard](https://github.com/Lombiq/Orchard)입니다!

## Dashboard view
<img width="1199" alt="image" src="https://user-images.githubusercontent.com/68543150/227722276-d4940c03-fbce-4909-b26f-9f5d6be814c4.png">



## Initialization

### 1. Install dependencies
Airflow DAG를 개발하기 위한 환경설정을 합니다.
```
$ virtualenv venv --python=python3.10
$ source venv/bin/activate
(venv)$ pip install -r requirements.txt
(venv)$ pip install -r requirements-dev.txt
(venv)$ deactivate
```


### 2. Terraform
Terraform에서는 총 5개의 리소스를 프로비저닝합니다.
1. 추출한 데이터를 저장할 GCS 버킷
2. 위 GCS버킷을 외부 저장소로 바라보는 BigQuery 데이터셋과 테이블
3. DBT 결과물을 저장하는 데이터셋과 테이블
```
$ cd terraform
$ terraform init
$ terraform plan -var="project=<your-gcp-project-id>"
$ terraform apply -var="project=<your-gcp-project-id>"
```


### 3. Airflow
Airflow가 실행되는 VM은 Terraform으로 프로비저닝하지 않고 콘솔에서 생성했습니다.

Airflow를 VM에 설치하는 방법은 Max님의 문서를 참조했습니다. 링크:
https://github.com/keeyong/data-engineering-batch12/blob/main/docs/Airflow%202%20Installation.md

## Details for the project

### Github Archive Events Data Pipeline
- Pipeline Flow

  ![zoomcamp drawio](https://user-images.githubusercontent.com/68543150/227722102-39611cfc-6c21-4b46-85d5-8fa497fb10f0.svg)
- DAG View

  ![dag](https://user-images.githubusercontent.com/68543150/227722476-3ff3a70d-51c3-47bc-b6ba-e42409d47062.png)
- DAG Grid View

  ![dag_grid](https://user-images.githubusercontent.com/68543150/227722450-46329525-f7d3-4a34-8121-dcba843ebd94.png)
- DAG Graph View

  <img width="1424" alt="image" src="https://user-images.githubusercontent.com/68543150/227723972-6248094c-61a0-4520-a880-73802a695607.png">
[Airflow DAG File](dags/etl_web_to_gcs.py)

Github Archive에서 매시 30분마다 데이터를 가져옵니다.

가져온 데이터에서 `payload` 필드는 사용하지 않기 때문에 제외하고, 문자열로된 `created_at` 필드를 타임스탬프로 변환한 후 parquet로 저장합니다. 이 작업은 DuckDB로 수행했습니다. 

DuckDB는 DataFrame API 보다 SQL이 익숙한 사람이 더 쉽게 데이터를 가공할 수 있게 해주는 오픈소스입니다.

Pandas보다 메모리 효율적으로 작동하며, Polars보다는 성능이 떨어진다는 여러 블로그 포스트를 봤지만, Airflow에서 Polars를 사용하면 `Exit With Return code 2`와 유사한 에러를 발생시킵니다. 제가 확인한 바로는 해결방법이 없어 Polars에서 DuckDB로 변경하였고 결과는 매우 만족스러웠습니다 :) (사실 컴퓨팅 작업은 Airflow 인스턴스가 아닌 외부에서 작동하게끔 하는 것이 바람직합니다. 그러나 저는 DAG가 단 하나이기 때문에 외부에서 작업하는 것이 오버헤드가 높다고 판단했습니다.)

이후 parquet 파일을 GCS에 로드하는데, BigQuery 외부테이블이 파티셔닝 가능하게 Hive partitioning 형태로 저장합니다. 여기서는 `year`, `month`, `day`에 대한 Hive partition을 지정합니다. (`year={year}/month={month}/day={day}`)

이렇게 하면 외부테이블에서도 `WHERE`절을 통해 데이터를 불러오는 비용을 절약할 수 있습니다.

아래 사진은 정상적으로 외부 테이블에 파티셔닝이 적용된 모습을 보여줍니다. (바이트 279MB -> 52MB, `year`, `month`, `day`는 기존 데이터의 컬럼이 아닌 파티션 프리픽스입니다.)

- NO `WHERE` statement
  
  <img width="531" alt="image" src="https://user-images.githubusercontent.com/68543150/227723711-c9e5e5d6-b3c4-45e6-8c1a-669d47fdb312.png">

- With `Where` statement

  <img width="552" alt="image" src="https://user-images.githubusercontent.com/68543150/227723676-95286b36-cbca-47a2-8679-b7ee7aba2013.png">


Airflow DAG 파일에 대한 별도의 CI/CD 파이프라인은 구축하지 않았고, 파일을 푸시하면 VM 내에서 풀하는 방식으로 코드를 업데이트 했습니다.
```
$ sudo su airflow

$ cd GHArchive-Data-Pipeline-Project/ && \
  git pull && \
  cd .. && \
  cp -r GHArchive-Data-Pipeline-Project/dags/* dags/
```

### Why Not Use Prefect?
처음엔 Prefect로 진행을 시도했는데, 일단 문서가 너무 불친절했습니다. 

VM에 올리는 문서도 현재 제공되지 않고 있고, 관련 커뮤니티도 너무 작았습니다. 

이대로 가단 프로젝트를 완성 못시킬 수도 있겠다 싶어 과감하게 Prefect를 버리고 좀 더 친숙한 Airflow로 옮겼습니다.

제 생각엔 Prefect는 Airflow의 New Replacement가 될 순 없을 것 같습니다. (솔직히 너무 구려요. 나은게 없음)

## DBT
DBT 관련 문서는 [여기](gh_dbt/README-KR.md)를 참조하세요.

## Relative Links
- 데이터셋 링크: https://www.gharchive.org/
- 대시보드 링크(공식 프로젝트 마감 기한이 끝나면 링크를 없앨 예정입니다.): https://lookerstudio.google.com/reporting/f9c69c6f-6165-4c91-a8a8-a02b75c0c9f6/page/dtGKD
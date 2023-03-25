# Github Archive Data Pipeline Project

If you're more comfortable with Korean, see [here](./readme-KR.md).

## Dashboard view
<img width="1199" alt="image" src="https://user-images.githubusercontent.com/68543150/227722276-d4940c03-fbce-4909-b26f-9f5d6be814c4.png">



## Initialization

### 1. Install dependencies
Set up your environment to develop an Airflow DAG.
```
$ virtualenv venv --python=python3.10
$ source venv/bin/activate
(venv)$ pip install -r requirements.txt
(venv)$ pip install -r requirements-dev.txt
(venv)$ deactivate
```


### 2. Terraform
Terraform provisions a total of five resources.
1. a GCS bucket to store the extracted data
2. a BigQuery dataset and table looking at the above GCS bucket as external storage
3. a dataset and table to store the DBT output
```
$ cd terraform
$ terraform init
$ terraform plan -var="project=<your-gcp-project-id>"
$ terraform apply -var="project=<your-gcp-project-id>"
```


### 3. Airflow
The VM running Airflow was created from the console, not provisioned with Terraform.

I referenced Max's article on how to install Airflow on a VM. Link:
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

Fetch data from the Github Archive every 30 minutes on the hour.

From the imported data, exclude the `payload` field because I don't use it, convert the `created_at` field as a string to a timestamp, and save it as a parquet. 
I did this with DuckDB. 

DuckDB is an open source that makes data processing easier for people familiar with SQL than the DataFrame API.

I've seen several blog posts that say it's more memory efficient than Pandas and less performant than Polars, but using Polars in Airflow throws an error similar to `Exit With Return code 2`. As far as I could see, there was no workaround, so I switched from Polars to DuckDB and was very happy with the results :) (Actually, it's preferable to have the compute work outside of the Airflow instance, but I decided that since I only have one DAG, it would be overhead to work outside).

The parquet file is then loaded into GCS, which stores it as a Hive partitioning so that the BigQuery external table can be partitioned. Here I specified Hive partitions for `year`, `month`, and `day`: (`year={year}/month={month}/day={day}`)

This saves the cost of fetching data from the external table via the `WHERE` clause.

The photo below shows the partitioning applied to the external table as normal. (Bytes 279MB -> 52MB, `year`, `month`, `day` are partition prefixes, not columns in the existing data).

- NO `WHERE` statement
<img width="531" alt="image" src="https://user-images.githubusercontent.com/68543150/227723711-c9e5e5d6-b3c4-45e6-8c1a-669d47fdb312.png">

- With `Where` statement
<img width="552" alt="image" src="https://user-images.githubusercontent.com/68543150/227723676-95286b36-cbca-47a2-8679-b7ee7aba2013.png">


I didn't build a separate CI/CD pipeline for the Airflow DAG file, I just updated the code by pushing the file and pulling it from within the VM.
```
$ sudo su airflow

$ cd GHArchive-Data-Pipeline-Project/ && \
  git pull && \
  cd .. && \
  cp -r GHArchive-Data-Pipeline-Project/dags/* dags/
```

### Why Not Use Prefect?
I initially tried Prefect, but the documentation was too unfriendly. 

The documentation for uploading to a VM is not currently available, and the community was too small. 

I realized that I might not be able to finish my malleable project, so I took the plunge and abandoned Prefect and moved to the more familiar Airflow.

In my opinion, Prefect will never be the new replacement for Airflow (honestly, it just sucks, there's nothing better).

## DBT
See [here](gh_dbt/README.md) for DBT-related documentation.

## Relative Links
- Dataset Link: https://www.gharchive.org/
- Dashboard link (I will remove the link once the official project deadline is over): https://lookerstudio.google.com/reporting/f9c69c6f-6165-4c91-a8a8-a02b75c0c9f6/page/dtGKD
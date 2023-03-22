import os
import gzip
import json
from datetime import datetime

# from urllib import request
import requests

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import (
    LocalFilesystemToGCSOperator,
)

default_args = {
    "owner": "airflow",
    "catchup": False,
}


@dag(
    default_args=default_args,
    start_date=datetime(2023, 3, 1),
    schedule_interval="30 * * * *",
    tags=["etl", "gcs"],
)
def etl_web_to_gcs_dag():
    @task()
    def start(**context):
        year, month, day = map(int, context["ds"].split("-"))

        dir_name = f"data/{year}/{month:02d}/{day:02d}"

        os.makedirs(f"/tmp/{dir_name}", exist_ok=True)
        return dir_name

    @task()
    def get_file_json_gz_path(**context):
        hour = context["ts_nodash"].split("T")[1][:2]
        dir_name = context["ti"].xcom_pull(task_ids="start")
        return f"{dir_name}/{hour}.json.gz"

    @task()
    def get_file_parquet_path(**context):
        hour = context["ts_nodash"].split("T")[1][:2]
        dir_name = context["ti"].xcom_pull(task_ids="start")
        return f"{dir_name}/{hour}.parquet"

    @task(retries=1)
    def extract_data_from_web(**context) -> None:
        year, month, day = map(int, context["ds"].split("-"))
        hour = int(context["ts_nodash"].split("T")[1][:2])

        headers = {"User-Agent": "Mozilla/5.0"}

        # hour is 0-23
        url = f"https://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour}.json.gz"
        print(f"Extracting data from {url}...")
        data = requests.get(url, headers=headers).content

        file_name = context["ti"].xcom_pull(
            task_ids="get_file_json_gz_path"
        )
        print(f"file name: {file_name}")

        with open(f"/tmp/{file_name}", "wb") as outfile:
            outfile.write(data)

    @task()
    def transform_data(**context):
        import duckdb
        from schema.schema_duckdb import DUCKDB_SCHEMA

        file_path = context["ti"].xcom_pull(
            task_ids="get_file_json_gz_path"
        )

        df = duckdb.sql(
            f"""
                select
                    id,
                    type,
                    actor,
                    repo,
                    strptime(created_at, '%Y-%m-%dT%H:%M:%SZ') as created_at,
                from read_ndjson('/tmp/{file_path}', columns={DUCKDB_SCHEMA})
            """
        )

        parquet_path = file_path.replace(".json.gz", ".parquet")

        duckdb.sql(
            f"""
            copy df 
            to '/tmp/{parquet_path}' (format parquet)
            """
        )

    load_to_gcs = LocalFilesystemToGCSOperator(
        task_id="load_to_gcs",
        src="/tmp/{{ ti.xcom_pull(task_ids='get_file_parquet_path') }}",
        dst="{{ ti.xcom_pull(task_ids='get_file_parquet_path') }}",
        bucket="github_data_silken-quasar-350808",
    )

    clean_up_json_gz = BashOperator(
        task_id="clean_up_json_gz",
        bash_command="rm -rf /tmp/{{ ti.xcom_pull(task_ids='get_file_json_gz_path') }}",
    )

    clean_up_parquet = BashOperator(
        task_id="clean_up_parquet",
        bash_command="rm -rf /tmp/{{ ti.xcom_pull(task_ids='get_file_parquet_path') }}",
    )

    start = start()
    (
        start
        >> [get_file_json_gz_path(), get_file_parquet_path()]
        >> extract_data_from_web()
        >> transform_data()
        >> load_to_gcs
        >> [clean_up_json_gz, clean_up_parquet]
    )


etl_web_to_gcs_dag()

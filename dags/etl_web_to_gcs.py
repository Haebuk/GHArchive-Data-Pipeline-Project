import os
import gzip
import json
from datetime import datetime
from urllib import request

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
    def get_file_path(**context):
        hour = context["ts_nodash"].split("T")[1][:2]
        dir_name = context["ti"].xcom_pull(task_ids="start")
        return f"{dir_name}/{hour}.json.gz"

    @task(retries=2)
    def extract_data_from_web(**context) -> None:
        year, month, day = map(int, context["ds"].split("-"))
        hour = int(context["ts_nodash"].split("T")[1][:2])

        headers = {"User-Agent": "Mozilla/5.0"}

        # hour is 0-23
        url = f"https://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour}.json.gz"
        print(f"Extracting data from {url}...")
        req = request.Request(url, headers=headers)
        response = request.urlopen(req)

        data = gzip.decompress(response.read()).decode()

        dicts = data.strip().split("\n")

        data_list = []
        for d in dicts:
            # remove payload key in dict
            d = json.loads(d)
            d.pop("payload")
            data_list.append(d)

        file_name = context["ti"].xcom_pull(task_ids="get_file_path")
        print(f"file name: {file_name}")

        with gzip.open(f"/tmp/{file_name}", "wt", encoding="utf-8") as f:
            json.dump(data_list, f)

    load_to_gcs = LocalFilesystemToGCSOperator(
        task_id="load_to_gcs",
        src="/tmp/{{ ti.xcom_pull(task_ids='get_file_path') }}",
        dst="{{ ti.xcom_pull(task_ids='get_file_path') }}",
        bucket="github_data_silken-quasar-350808",
    )

    clean_up = BashOperator(
        task_id="clean_up",
        bash_command="rm -rf /tmp/{{ ti.xcom_pull(task_ids='get_file_path') }}",
    )

    (
        start()
        >> get_file_path()
        >> extract_data_from_web()
        >> load_to_gcs
        >> clean_up
    )


etl_web_to_gcs_dag()

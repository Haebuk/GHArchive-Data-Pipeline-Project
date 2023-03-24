import os
from datetime import datetime
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
    start_date=datetime(2023, 3, 20),
    schedule_interval="30 * * * *",
    tags=["etl", "gcs"],
)
def etl_github_archive_data_to_gcs_dag():
    @task()
    def start(**context) -> dict[str, str]:
        year, month, day = map(int, context["ds"].split("-"))

        local_dir_name = f"/tmp/data/{year}/{month:02d}/{day:02d}"
        gcs_dir_name = f"data/year={year}/month={month:02d}/day={day:02d}"

        os.makedirs(f"{local_dir_name}", exist_ok=True)
        return {
            "local_dir_name": local_dir_name,
            "gcs_dir_name": gcs_dir_name,
        }

    @task()
    def get_file_paths(dir_name_dict, **context) -> dict[str, str]:
        hour = context["ts_nodash"].split("T")[1][:2]

        local_dir = dir_name_dict["local_dir_name"]
        gcs_dir = dir_name_dict["gcs_dir_name"]

        local_json_gz_path = f"{local_dir}/{hour}.json.gz"
        local_parquet_path = f"{local_dir}/{hour}.parquet"
        gcs_parquet_path = f"{gcs_dir}/{hour}.parquet"

        return {
            "local_json_gz_path": local_json_gz_path,
            "local_parquet_path": local_parquet_path,
            "gcs_parquet_path": gcs_parquet_path,
        }

    @task(retries=1)
    def extract_data_from_web(local_json_gz_path, **context) -> None:
        year, month, day = map(int, context["ds"].split("-"))
        hour = int(context["ts_nodash"].split("T")[1][:2])

        headers = {"User-Agent": "Mozilla/5.0"}

        # hour is 0-23
        url = f"https://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour}.json.gz"
        print(f"Extracting data from {url}...")
        data = requests.get(url, headers=headers).content

        with open(local_json_gz_path, "wb") as outfile:
            outfile.write(data)

    @task()
    def transform_data(local_json_gz_path, local_parquet_path):
        import duckdb
        from schema.schema_duckdb import DUCKDB_SCHEMA

        df = duckdb.sql(
            f"""
                select
                    id,
                    type,
                    actor,
                    repo,
                    strptime(created_at, '%Y-%m-%dT%H:%M:%SZ') as created_at,
                from read_ndjson('{local_json_gz_path}', columns={DUCKDB_SCHEMA}, maximum_object_size=2000000)
            """
        )

        df.show()

        duckdb.sql(
            f"""
            copy df 
            to '{local_parquet_path}' (format parquet)
            """
        )

    load_to_gcs = LocalFilesystemToGCSOperator(
        task_id="load_to_gcs",
        src="{{ ti.xcom_pull(task_ids='get_file_paths', key='local_parquet_path') }}",
        dst="{{ ti.xcom_pull(task_ids='get_file_paths', key='gcs_parquet_path') }}",
        bucket="github_data_silken-quasar-350808",
    )

    clean_up_json_gz = BashOperator(
        task_id="clean_up_json_gz",
        bash_command="rm -rf {{ ti.xcom_pull(task_ids='get_file_paths', key='local_json_gz_path') }}",
    )

    clean_up_parquet = BashOperator(
        task_id="clean_up_parquet",
        bash_command="rm -rf {{ ti.xcom_pull(task_ids='get_file_paths', key='local_parquet_path') }}",
    )

    get_dir_name_dict = start()
    get_file_path_dict = get_file_paths(get_dir_name_dict)
    (
        get_dir_name_dict
        >> get_file_path_dict
        >> extract_data_from_web(get_file_path_dict["local_json_gz_path"])
        >> transform_data(
            get_file_path_dict["local_json_gz_path"],
            get_file_path_dict["local_parquet_path"],
        )
        >> load_to_gcs
        >> clean_up_json_gz
        >> clean_up_parquet
    )


etl_github_archive_data_to_gcs_dag()

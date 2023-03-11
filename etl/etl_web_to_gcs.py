import os
import gzip
import json
from urllib import request
from datetime import timedelta

import polars as pl
from prefect import flow, task
from prefect.tasks import task_input_hash
from prefect_gcp.cloud_storage import GcsBucket


@task(
    retries=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1),
)
def extract_data_from_web(
    year: int, month: int, day: int, hour: int
) -> list[str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    # hour is 0-23
    url = f"https://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour}.json.gz"

    req = request.Request(url, headers=headers)
    response = request.urlopen(req)

    data = gzip.decompress(response.read()).decode()

    return data


@task()
def transform_data(data: list[str], to_path: str) -> list[dict]:
    from schema.schema_polars import PL_SCHEMA

    dicts = data.strip().split("\n")

    data_list = [json.loads(d) for d in dicts]

    df = pl.from_dicts(data_list, schema=PL_SCHEMA)

    df = df.drop(["public", "payload"])

    df.write_parquet(to_path)


@task()
def load_to_gcs(file_path: str) -> None:
    # dir = f"data/{year}/{month:02d}/{day:02d}"

    # os.makedirs(dir, exist_ok=True)

    # df.write_parquet(file_path)

    gcs_bucket = GcsBucket.load("github-gcs")
    gcs_bucket.upload_from_path(
        from_path=file_path,
        to_path=file_path,
    )

    # os.remove(file_path)

    print(f"File {file_path} uploaded to GCS.")


@flow()
def etl_web_to_gcs(
    year: int = 2023,
    months: list[int] = None,
    days: list[int] = None,
    hours: list[int] = None,
) -> None:
    for month in months:
        for day in days:
            for hour in hours:
                dir_name = f"data/{year}/{month:02d}/{day:02d}"
                if os.path.exists(f"{dir_name}/{hour:02d}.parquet"):
                    continue
                data = extract_data_from_web(year, month, day, hour)
                transform_data(
                    data, to_path=f"{dir_name}/{hour:02d}.parquet"
                )
                load_to_gcs(file_path=f"{dir_name}/{hour:02d}.parquet")


if __name__ == "__main__":
    months = [1]
    days = [i for i in range(1, 32)]
    hours = [i for i in range(24)]
    etl_web_to_gcs(
        year=2023,
        months=months,
        days=days,
        hours=hours,
    )

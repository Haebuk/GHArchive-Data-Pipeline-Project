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
def load_data_from_web(
    year: int, month: int, day: int, hour: int
) -> list[str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour}.json.gz"  # hour is 0-24

    req = request.Request(url, headers=headers)
    response = request.urlopen(req)

    data = gzip.decompress(response.read()).decode()

    return data


@task()
def concat_data(data: list[str]) -> list[dict]:
    dicts = data.strip().split("\n")

    data_list = [json.loads(d) for d in dicts]

    return data_list


@task()
def transform_data(data: list[dict]) -> pl.DataFrame:
    from schema.schema_polars import PL_SCHEMA

    df = pl.from_dicts(data, schema=PL_SCHEMA)

    df = df.with_columns(
        df["created_at"]
        .str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%SZ")
        .alias("created_at")
    ).drop("public")

    return df


@task()
def load_to_gcs(
    df: pl.DataFrame, year: int, month: int, day: int, hour: int
) -> None:
    dir = f"data/{year}/{month:02d}/{day:02d}"
    file_path = f"{dir}/{hour:02d}.parquet"

    os.makedirs(dir, exist_ok=True)

    df.write_parquet(file_path)

    gcs_bucket = GcsBucket.load("github-gcs")
    gcs_bucket.put_directory(local_path=file_path, to_path=file_path)

    os.remove(file_path)

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
                data = load_data_from_web(year, month, day, hour)
                data_list = concat_data(data)
                df = transform_data(data_list)
                load_to_gcs(df, year, month, day, hour)


if __name__ == "__main__":
    etl_web_to_gcs(
        year=2023,
        months=[1],
        days=[1],
        hours=[1],
    )

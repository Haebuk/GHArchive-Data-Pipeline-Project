import os
import gzip
import json
import pendulum
from datetime import timedelta
from urllib import request

from prefect.context import get_run_context
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
) -> None:
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

    file_name = f"data/{year}/{month:02d}/{day:02d}/{hour:02d}.json.gz"
    with gzip.open(file_name, "wt", encoding="utf-8") as f:
        json.dump(data_list, f)


@task(retries=2)
def load_to_gcs(file_path: str) -> None:
    gcs_bucket = GcsBucket.load("github-gcs")
    gcs_bucket.upload_from_path(
        from_path=file_path,
        to_path=file_path,
    )

    # os.remove(file_path)

    print(f"File {file_path} uploaded to GCS.")


@flow()
def etl_web_to_gcs(
    execution_date: str = None,
) -> None:
    if execution_date is None:
        # default to 1 hour ago. github data not avaialble for current hour
        execution_date = get_run_context().start_time - timedelta(hours=1)
    else:
        execution_date = pendulum.from_format(
            execution_date, "YYYY-MM-DD-HH"
        )

    year = execution_date.year
    month = execution_date.month
    day = execution_date.day
    hour = execution_date.hour

    print(f"execution_date: {year}-{month:02d}-{day:02d}-{hour:02d}")

    dir_name = f"data/{year}/{month:02d}/{day:02d}"

    os.makedirs(dir_name, exist_ok=True)
    extract_data_from_web(year, month, day, hour)
    load_to_gcs(file_path=f"{dir_name}/{hour:02d}.json.gz")


if __name__ == "__main__":
    etl_web_to_gcs()

import polars as pl
from prefect import flow, task


@flow()
def etl_web_to_gcs() -> None:
    print("hello world!")


if __name__ == "__main__":
    etl_web_to_gcs()

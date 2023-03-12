from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from etl_web_to_gcs import etl_web_to_gcs

deploy_etl_web_to_gcs = Deployment.build_from_flow(
    flow=etl_web_to_gcs,
    name="github_etl_web_to_gcs",
    schedule=(CronSchedule(cron="30 * * * *")),
)

if __name__ == "__main__":
    deploy_etl_web_to_gcs.apply()

# Github Archive Data Pipeline Project
- My Dataset Link: https://www.gharchive.org/
- Dataset schema: https://github.com/igrigorik/gharchive.org/blob/master/bigquery/schema.js



## Initialization

### 1. Install dependencies
```
$ virtualenv venv --python=python3.10
$ source venv/bin/activate
(venv)$ pip install -r requirements.txt
(venv)$ pip install -r requirements-dev.txt
(venv)$ deactivate

$ virtualenv venv-dbt --python=python3.10
$ source venv-dbt/bin/activate
(venv-dbt)$ pip install -r requirements-dbt.txt
(venv-dbt)$ deactivate
```

### 2. Terraform
```
$ cd terraform
$ terraform init
$ terraform plan -var="project=<your-gcp-project-id>"
$ terraform apply -var="project=<your-gcp-project-id>"
```

### 3. Prefect
Create an workspace in Prefect cloud, 
then activate the venv and set the workspace.

Make the GCP Credentials block and GCS Bucket block. 
these blocks are used to ETL pipeline in the Prefect.


### 4. VM
```
$ sudo apt-get update
$ sudo apt-get install -y libbz2-dev build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev  wget libsqlite3-dev
$ wget https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz
$ tar -xf Python-3.11.2.tar.xz
$ cd Python-3.11.2
$ ./configure --enable-optimizations
$ sudo make altinstall
```

```
$ prefect cloud login -k {MYAPIKEY}
$ prefect agent start -p default-agent-pool
```

- todo: vm에 코드를 디플로이 할 수 있도록 ci/cd 환경 구성하기.
- https://docs.prefect.io/concepts/deployments/

```
prefect deployment build etl/etl_web_to_gcs.py:etl_web_to_gcs -n etl_github_data_to_gcs -p gh-agent-pool -q default -sb gcs-bucket/github-flow --cron "30 * * * *" -a
```
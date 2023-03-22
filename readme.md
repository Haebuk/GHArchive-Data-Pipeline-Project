# Github Archive Data Pipeline Project
- My Dataset Link: https://www.gharchive.org/
- Dataset schema: https://github.com/igrigorik/gharchive.org/blob/master/bigquery/schema.js

```
wget https://data.gharchive.org/2023-03-{17..19}-{0..23}.json.gz
```

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

### 3. Airflow
https://github.com/keeyong/data-engineering-batch11/blob/main/docs/Airflow%202%20Installation.md
```
sudo pip3 install --ignore-installed "apache-airflow[celery]==2.5.1" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.5.1/constraints-3.7.txt"
```


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
- login prefect cloud in vm
```
$ prefect cloud login -k {MYAPIKEY}
```

```
gcloud compute instances create-with-container prefect-agent-server \
		--container-image prefecthq/prefect:2-python3.10 \
		--container-mount-host-path=host-path=/var/run/docker.sock,mount-path=/var/run/docker.sock,mode=rw \
		--container-privileged \
		--container-env PREFECT_API_URL=${PREFECT_API_URL} \
		--container-env PREFECT_API_KEY=${PREFECT_API_KEY} \
		--container-command="prefect" \
		--container-arg="agent" \
		--container-arg="start" \
        --container-arg="-p" \
        --container-arg="gh-agent-pool" \
		--container-arg="-q" \
		--container-arg="default" \
		--container-restart-policy='always' \
		--boot-disk-size="100Gi" \
		--machine-type="e2-medium" \
		--zone="asia-northeast3-a"

```

## Deployment
```
cd GHArchive-Data-Pipeline-Project/ && git pull && cd .. && cp -r GHArchive-Data-Pipeline-Project/dags/* dags/
```


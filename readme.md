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

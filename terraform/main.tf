terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
}

resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}_${var.project}" # Concatenating DL bucket & Project name for unique naming
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = false
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = false
}

# DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.bigquery_dataset
  project    = var.project
  location   = var.region
}   
resource "google_bigquery_dataset" "dbt_dataset" {
  dataset_id = var.bigquery_dataset_dbt
  project    = var.project
  location   = var.region
}   

# External Table
resource "google_bigquery_table" "gharchive" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "gharchive"

  

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"

    source_uris = [
      "gs://${local.data_lake_bucket}_${var.project}/data/*",
    ]

    hive_partitioning_options {
      mode = "AUTO"
      source_uri_prefix = "gs://${local.data_lake_bucket}_${var.project}/data/"
    }
  }
}
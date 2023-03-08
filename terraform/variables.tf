locals {
  data_lake_bucket = "github_data"
}

variable project {
  type        = string
  description = "GCP Project ID"
}

variable region {
  type        = string
  default     = "asia-northeast3"
  description = "region for GCP"
}

variable bigquery_dataset {
  type        = string
  default     = "github_dataset"
  description = "BigQuery dataset that raws data will be written to"
}

variable storage_class {
  type        = string
  default     = "STANDARD"
  description = "Storage class type"
}

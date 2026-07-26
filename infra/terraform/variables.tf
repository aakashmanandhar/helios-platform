variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "helios-platform-aakash"
}

variable "region" {
  description = "Default region for BigQuery datasets"
  type        = string
  default     = "us-central1"
}

variable "bucket_location" {
  description = "GCS bucket location (as reported by gcloud, uppercase form)"
  type        = string
  default     = "US-CENTRAL1"
}

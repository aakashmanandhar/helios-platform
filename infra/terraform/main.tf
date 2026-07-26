resource "google_storage_bucket" "lake" {
  name                        = "${var.project_id}-lake"
  location                    = var.bucket_location
  storage_class                = "STANDARD"
  uniform_bucket_level_access = false
  force_destroy                = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_bigquery_dataset" "bronze" {
  dataset_id = "bronze"
  project    = var.project_id
  location   = var.region

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_bigquery_dataset" "silver" {
  dataset_id = "silver"
  project    = var.project_id
  location   = var.region

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_bigquery_dataset" "gold" {
  dataset_id = "gold"
  project    = var.project_id
  location   = var.region

  lifecycle {
    prevent_destroy = true
  }
}

terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

variable "service_name" {
  type    = string
  default = "cloud-run-service"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "container_image" {
  type = string
}

variable "container_env" {
  type    = map(string)
  default = {}
}

variable "secret_env" {
  description = "Map of environment variable names to Secret Manager secret versions"
  type        = map(string)
  default     = {}
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "vpc_network" {
  description = "VPC network for the connector"
  type        = string
}

variable "connector_cidr" {
  description = "CIDR range for the VPC connector"
  type        = string
  default     = "10.8.0.0/28"
}

resource "google_service_account" "service" {
  account_id   = var.service_name
  display_name = var.service_name
}

resource "google_project_iam_member" "secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.service.email}"
}

resource "google_vpc_access_connector" "connector" {
  name          = "${var.service_name}-connector"
  network       = var.vpc_network
  region        = var.region
  ip_cidr_range = var.connector_cidr
}

resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image

        dynamic "env" {
          for_each = var.container_env
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = var.secret_env
          content {
            name = env.key
            value_from {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }
      }
    }

    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.id
      }
    }
  }

  traffics {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
  project                    = var.project_id
  depends_on = [
    google_project_iam_member.secret_access,
    google_vpc_access_connector.connector
  ]
}

output "url" {
  value = google_cloud_run_service.service.status[0].url
}

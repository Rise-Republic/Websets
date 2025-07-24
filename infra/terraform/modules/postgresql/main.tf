terraform {
  required_providers {
    helm = {
      source = "hashicorp/helm"
    }
  }
}

variable "namespace" {
  type        = string
  default     = "default"
}

variable "name" {
  type        = string
  default     = "postgresql"
}

resource "helm_release" "postgresql" {
  name       = var.name
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  namespace  = var.namespace
}

output "service_name" {
  value = helm_release.postgresql.name
}

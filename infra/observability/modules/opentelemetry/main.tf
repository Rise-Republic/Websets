terraform {
  required_providers {
    helm = {
      source = "hashicorp/helm"
    }
  }
}

variable "namespace" {
  type        = string
  default     = "observability"
}

variable "name" {
  type    = string
  default = "otel-collector"
}

resource "helm_release" "otel_collector" {
  name       = var.name
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  namespace  = var.namespace
  values     = [file("${path.module}/values.yml")]
}

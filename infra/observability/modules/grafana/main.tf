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
  default = "grafana"
}

resource "helm_release" "grafana" {
  name       = var.name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  namespace  = var.namespace
  values     = [file("${path.module}/values.yml")]
}

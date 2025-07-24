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
  default = "prometheus"
}

resource "helm_release" "prometheus" {
  name       = var.name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  namespace  = var.namespace
  values     = [file("${path.module}/values.yml")]
}

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
  default = "alertmanager"
}

resource "helm_release" "alertmanager" {
  name       = var.name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "alertmanager"
  namespace  = var.namespace
  values     = [file("${path.module}/values.yml")]
}

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
  default     = "redis"
}

resource "helm_release" "redis" {
  name       = var.name
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  namespace  = var.namespace
}

output "service_name" {
  value = helm_release.redis.name
}

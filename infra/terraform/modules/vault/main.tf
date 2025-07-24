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
  default     = "vault"
}

resource "helm_release" "vault" {
  name       = var.name
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  namespace  = var.namespace
}

output "service_name" {
  value = helm_release.vault.name
}

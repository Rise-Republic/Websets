terraform {
  required_version = ">= 1.5"
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.2"
    }
  }
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}

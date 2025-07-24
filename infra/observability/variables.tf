variable "kubeconfig" {
  description = "Path to kubeconfig file"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for observability components"
  type        = string
  default     = "observability"
}

variable "grafana_url" {
  description = "Base URL for Grafana API"
  type        = string
  default     = "http://localhost:3000"
}

variable "grafana_auth" {
  description = "Grafana authentication string (token or user:pass)"
  type        = string
  sensitive   = true
}

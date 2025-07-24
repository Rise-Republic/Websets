variable "kubeconfig" {
  description = "Path to kubeconfig file"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for observability components"
  type        = string
  default     = "observability"
}

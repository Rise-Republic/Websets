variable "kubeconfig" {
  description = "Path to kubeconfig file"
  type        = string
}

variable "aws_region" {
  description = "AWS region for cluster module"
  type        = string
  default     = "us-east-1"
}

variable "namespace" {
  description = "Kubernetes namespace to deploy services"
  type        = string
  default     = "default"
}

variable "cluster_name" {
  description = "Name of Kubernetes cluster"
  type        = string
  default     = "webset-cluster"
}

variable "vpc_id" {
  description = "VPC ID for cluster networking"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for the cluster"
  type        = list(string)
}

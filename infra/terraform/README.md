# Terraform Infrastructure

This directory contains Terraform modules for setting up the WebSet Miner
infrastructure. The modules provision a Kubernetes cluster along with
PostgreSQL, Redis, and Vault using Helm charts.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.5
- Access to an AWS account (for the sample EKS configuration)
- `kubectl` configured for your cluster

## Quick Start

1. Change into the Terraform directory:
   ```bash
   cd infra/terraform
   ```
2. Initialize the modules and download providers:
   ```bash
   terraform init
   ```
3. Review the execution plan:
   ```bash
   terraform plan \
     -var="kubeconfig=$HOME/.kube/config" \
     -var="vpc_id=<vpc-id>" \
     -var="subnet_ids=[\"subnet-abc\",\"subnet-def\"]"
   ```
4. Apply the configuration:
   ```bash
   terraform apply \
     -var="kubeconfig=$HOME/.kube/config" \
     -var="vpc_id=<vpc-id>" \
     -var="subnet_ids=[\"subnet-abc\",\"subnet-def\"]"
   ```

This will create or update the cluster and deploy PostgreSQL, Redis,
and Vault into the specified namespace.

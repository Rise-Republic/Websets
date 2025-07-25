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

## Fargate Service Module

The [`modules/fargate_service`](modules/fargate_service) module provisions an
AWS Fargate task behind an Application Load Balancer. Secrets required by the
container are read from **AWS Secrets Manager**.

### Example variable file

Create a file named `fargate.auto.tfvars`:

```hcl
service_name        = "webset-api"
vpc_id              = "vpc-123456"
subnet_ids          = ["subnet-abc", "subnet-def"]
container_image     = "ghcr.io/example/webset:latest"
secrets_manager_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:webset"
```

Then deploy with:

```bash
terraform init
terraform apply -var-file=fargate.auto.tfvars
```

## Cloud Run Service Module

The `modules/cloud_run_service` module deploys the WebSet container to
Google Cloud Run. Service configuration values can be stored in **Google Secret
Manager** and referenced in the module variables.

### Example variable file

Create a file named `cloudrun.auto.tfvars`:

```hcl
service_name    = "webset-api"
project_id      = "my-gcp-project"
region          = "us-central1"
container_image = "gcr.io/my-gcp-project/webset:latest"
secret_names    = ["webset-api-env"]
```

Then deploy with:

```bash
terraform init
terraform apply -var-file=cloudrun.auto.tfvars
```

## GitHub Actions

Deployment pipelines are defined in the GitHub Actions workflows:

- [`build-publish.yml`](../../.github/workflows/build-publish.yml) builds and
  pushes Docker images used by both modules.
- [`docker-deploy.yml`](../../.github/workflows/docker-deploy.yml) demonstrates
  how the image and secrets are consumed during deployment.

Store credentials in Secrets Manager or Google Secret Manager so the workflows
can inject them securely into the Terraform runs and services.

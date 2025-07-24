module "cluster" {
  source           = "./modules/k8s_cluster"
  cluster_name     = var.cluster_name
  cluster_version  = "1.27"
  vpc_id           = var.vpc_id
  subnet_ids       = var.subnet_ids
  region           = var.aws_region
}

module "postgresql" {
  source    = "./modules/postgresql"
  namespace = var.namespace
}

module "redis" {
  source    = "./modules/redis"
  namespace = var.namespace
}

module "vault" {
  source    = "./modules/vault"
  namespace = var.namespace
}

module "opentelemetry" {
  source    = "./modules/opentelemetry"
  namespace = var.namespace
}

module "prometheus" {
  source    = "./modules/prometheus"
  namespace = var.namespace
}

module "grafana" {
  source    = "./modules/grafana"
  namespace = var.namespace
}

module "alertmanager" {
  source    = "./modules/alertmanager"
  namespace = var.namespace
}

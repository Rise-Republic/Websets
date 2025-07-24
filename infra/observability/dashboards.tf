locals {
  dashboard_files = fileset("${path.module}/../../monitoring/grafana/dashboards", "*.json")
}

resource "grafana_dashboard" "dashboards" {
  for_each    = { for f in local.dashboard_files : f => f }
  config_json = file("${path.module}/../../monitoring/grafana/dashboards/${each.value}")
  overwrite   = true
}

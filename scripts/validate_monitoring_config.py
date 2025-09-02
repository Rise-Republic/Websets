#!/usr/bin/env python3
"""
Monitoring configuration validation script.
Validates Prometheus, Grafana, and AlertManager configurations.
"""

import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import jsonschema
import requests


class MonitoringValidator:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []

    def validate_prometheus_config(self) -> bool:
        """Validate Prometheus configuration files."""
        print("🔍 Validating Prometheus configuration...")
        
        config_file = self.base_path / "monitoring" / "prometheus" / "prometheus.yml"
        if not config_file.exists():
            self.errors.append(f"Prometheus config file not found: {config_file}")
            return False

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ["global", "scrape_configs", "rule_files"]
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"Missing required section in prometheus.yml: {section}")

            # Validate scrape configs
            if "scrape_configs" in config:
                for i, scrape_config in enumerate(config["scrape_configs"]):
                    if "job_name" not in scrape_config:
                        self.errors.append(f"Missing job_name in scrape_config {i}")
                    if "static_configs" not in scrape_config and "kubernetes_sd_configs" not in scrape_config:
                        self.warnings.append(f"No service discovery configured for job {scrape_config.get('job_name', i)}")

            print("✅ Prometheus configuration validation completed")
            return len(self.errors) == 0

        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in prometheus.yml: {e}")
            return False

    def validate_alert_rules(self) -> bool:
        """Validate Prometheus alert rules."""
        print("🔍 Validating alert rules...")
        
        rules_dir = self.base_path / "monitoring" / "prometheus" / "rules"
        if not rules_dir.exists():
            self.errors.append(f"Alert rules directory not found: {rules_dir}")
            return False

        rule_files = list(rules_dir.glob("*.yml")) + list(rules_dir.glob("*.yaml"))
        if not rule_files:
            self.warnings.append("No alert rule files found")
            return True

        for rule_file in rule_files:
            try:
                with open(rule_file) as f:
                    rules = yaml.safe_load(f)
                
                if "groups" not in rules:
                    self.errors.append(f"Missing 'groups' in {rule_file}")
                    continue

                for group in rules["groups"]:
                    if "name" not in group:
                        self.errors.append(f"Missing group name in {rule_file}")
                    if "rules" not in group:
                        self.errors.append(f"Missing rules in group {group.get('name', 'unnamed')} in {rule_file}")
                        continue

                    for rule in group["rules"]:
                        if "alert" in rule:
                            # Validate alert rule
                            required_fields = ["alert", "expr"]
                            for field in required_fields:
                                if field not in rule:
                                    self.errors.append(f"Missing {field} in alert rule in {rule_file}")
                            
                            if "labels" not in rule:
                                self.warnings.append(f"Alert {rule.get('alert', 'unnamed')} missing labels in {rule_file}")
                            if "annotations" not in rule:
                                self.warnings.append(f"Alert {rule.get('alert', 'unnamed')} missing annotations in {rule_file}")

            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML in {rule_file}: {e}")

        print("✅ Alert rules validation completed")
        return len(self.errors) == 0

    def validate_grafana_dashboards(self) -> bool:
        """Validate Grafana dashboard JSON files."""
        print("🔍 Validating Grafana dashboards...")
        
        dashboards_dir = self.base_path / "monitoring" / "grafana" / "dashboards"
        if not dashboards_dir.exists():
            self.errors.append(f"Grafana dashboards directory not found: {dashboards_dir}")
            return False

        dashboard_files = list(dashboards_dir.glob("*.json"))
        if not dashboard_files:
            self.warnings.append("No Grafana dashboard files found")
            return True

        for dashboard_file in dashboard_files:
            try:
                with open(dashboard_file) as f:
                    dashboard = json.load(f)
                
                # Validate dashboard structure
                if "dashboard" not in dashboard:
                    self.errors.append(f"Missing 'dashboard' object in {dashboard_file}")
                    continue

                dashboard_obj = dashboard["dashboard"]
                required_fields = ["title", "panels"]
                for field in required_fields:
                    if field not in dashboard_obj:
                        self.errors.append(f"Missing {field} in dashboard {dashboard_file}")

                # Validate panels
                if "panels" in dashboard_obj:
                    for i, panel in enumerate(dashboard_obj["panels"]):
                        if "id" not in panel:
                            self.errors.append(f"Missing id in panel {i} of {dashboard_file}")
                        if "title" not in panel:
                            self.warnings.append(f"Missing title in panel {i} of {dashboard_file}")
                        if "targets" not in panel:
                            self.warnings.append(f"Missing targets in panel {i} of {dashboard_file}")

            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {dashboard_file}: {e}")

        print("✅ Grafana dashboards validation completed")
        return len(self.errors) == 0

    def validate_alertmanager_config(self) -> bool:
        """Validate AlertManager configuration."""
        print("🔍 Validating AlertManager configuration...")
        
        config_file = self.base_path / "monitoring" / "alertmanager" / "alertmanager.yml"
        if not config_file.exists():
            self.warnings.append(f"AlertManager config file not found: {config_file}")
            return True

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ["route", "receivers"]
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"Missing required section in alertmanager.yml: {section}")

            # Validate route
            if "route" in config:
                route = config["route"]
                if "receiver" not in route:
                    self.errors.append("Missing receiver in root route")

            # Validate receivers
            if "receivers" in config:
                for receiver in config["receivers"]:
                    if "name" not in receiver:
                        self.errors.append("Missing name in receiver")

            print("✅ AlertManager configuration validation completed")
            return len(self.errors) == 0

        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in alertmanager.yml: {e}")
            return False

    def validate_kubernetes_manifests(self) -> bool:
        """Validate Kubernetes monitoring manifests."""
        print("🔍 Validating Kubernetes manifests...")
        
        monitoring_dir = self.base_path / "monitoring"
        manifest_files = []
        
        for subdir in ["prometheus", "grafana", "alertmanager"]:
            subdir_path = monitoring_dir / subdir
            if subdir_path.exists():
                manifest_files.extend(list(subdir_path.glob("*.yaml")))
                manifest_files.extend(list(subdir_path.glob("*.yml")))

        for manifest_file in manifest_files:
            if manifest_file.name in ["prometheus.yml", "alertmanager.yml"]:
                continue  # Skip config files, not K8s manifests
                
            try:
                with open(manifest_file) as f:
                    docs = list(yaml.safe_load_all(f))
                
                for doc in docs:
                    if not doc:
                        continue
                    
                    if "apiVersion" not in doc:
                        self.errors.append(f"Missing apiVersion in {manifest_file}")
                    if "kind" not in doc:
                        self.errors.append(f"Missing kind in {manifest_file}")
                    if "metadata" not in doc:
                        self.errors.append(f"Missing metadata in {manifest_file}")
                    elif "name" not in doc["metadata"]:
                        self.errors.append(f"Missing metadata.name in {manifest_file}")

            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML in {manifest_file}: {e}")

        print("✅ Kubernetes manifests validation completed")
        return len(self.errors) == 0

    def check_metric_consistency(self) -> bool:
        """Check consistency between dashboards and alert rules."""
        print("🔍 Checking metric consistency...")
        
        # Extract metrics from alert rules
        alert_metrics = set()
        rules_dir = self.base_path / "monitoring" / "prometheus" / "rules"
        if rules_dir.exists():
            for rule_file in rules_dir.glob("*.yml"):
                try:
                    with open(rule_file) as f:
                        rules = yaml.safe_load(f)
                    
                    for group in rules.get("groups", []):
                        for rule in group.get("rules", []):
                            if "expr" in rule:
                                # Simple metric extraction (could be more sophisticated)
                                expr = rule["expr"]
                                # Extract metric names (basic pattern matching)
                                import re
                                metrics = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', expr)
                                alert_metrics.update(metrics)
                except:
                    pass

        # Extract metrics from dashboards
        dashboard_metrics = set()
        dashboards_dir = self.base_path / "monitoring" / "grafana" / "dashboards"
        if dashboards_dir.exists():
            for dashboard_file in dashboards_dir.glob("*.json"):
                try:
                    with open(dashboard_file) as f:
                        dashboard = json.load(f)
                    
                    panels = dashboard.get("dashboard", {}).get("panels", [])
                    for panel in panels:
                        targets = panel.get("targets", [])
                        for target in targets:
                            if "expr" in target:
                                expr = target["expr"]
                                import re
                                metrics = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', expr)
                                dashboard_metrics.update(metrics)
                except:
                    pass

        # Check for common metrics
        common_metrics = alert_metrics.intersection(dashboard_metrics)
        if len(common_metrics) < 5:  # Arbitrary threshold
            self.warnings.append("Few common metrics between alerts and dashboards")

        print("✅ Metric consistency check completed")
        return True

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🚀 Starting monitoring configuration validation...\n")
        
        validations = [
            self.validate_prometheus_config,
            self.validate_alert_rules,
            self.validate_grafana_dashboards,
            self.validate_alertmanager_config,
            self.validate_kubernetes_manifests,
            self.check_metric_consistency,
        ]
        
        success = True
        for validation in validations:
            if not validation():
                success = False
            print()

        # Print summary
        print("📊 Validation Summary:")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if success and not self.errors:
            print("\n✅ All monitoring configurations are valid!")
        else:
            print("\n❌ Monitoring configuration validation failed!")
        
        return success and len(self.errors) == 0


def main():
    """Main function."""
    validator = MonitoringValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

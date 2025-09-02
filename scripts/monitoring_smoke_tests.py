#!/usr/bin/env python3
"""
Monitoring smoke tests to verify monitoring stack health.
"""

import requests
import time
import sys
import argparse
from typing import Dict, List, Tuple
import json


class MonitoringSmokeTests:
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.base_urls = {
            "staging": {
                "prometheus": "http://prometheus-staging:9090",
                "grafana": "http://grafana-staging:3000",
                "alertmanager": "http://alertmanager-staging:9093"
            },
            "production": {
                "prometheus": "http://prometheus:9090",
                "grafana": "http://grafana:3000",
                "alertmanager": "http://alertmanager:9093"
            }
        }
        self.results = []

    def test_prometheus_health(self) -> bool:
        """Test Prometheus health and basic functionality."""
        print("🔍 Testing Prometheus health...")
        
        base_url = self.base_urls[self.environment]["prometheus"]
        
        try:
            # Health check
            response = requests.get(f"{base_url}/-/healthy", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "Prometheus health check failed"))
                return False
            
            # Ready check
            response = requests.get(f"{base_url}/-/ready", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "Prometheus ready check failed"))
                return False
            
            # Test query API
            response = requests.get(
                f"{base_url}/api/v1/query",
                params={"query": "up"},
                timeout=10
            )
            if response.status_code != 200:
                self.results.append(("FAIL", "Prometheus query API failed"))
                return False
            
            data = response.json()
            if data["status"] != "success":
                self.results.append(("FAIL", "Prometheus query returned error"))
                return False
            
            # Check targets
            response = requests.get(f"{base_url}/api/v1/targets", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "Prometheus targets API failed"))
                return False
            
            targets_data = response.json()
            active_targets = [t for t in targets_data["data"]["activeTargets"] if t["health"] == "up"]
            if len(active_targets) == 0:
                self.results.append(("WARN", "No active Prometheus targets found"))
            
            self.results.append(("PASS", f"Prometheus health check passed ({len(active_targets)} targets up)"))
            return True
            
        except requests.RequestException as e:
            self.results.append(("FAIL", f"Prometheus connection failed: {e}"))
            return False

    def test_grafana_health(self) -> bool:
        """Test Grafana health and API."""
        print("🔍 Testing Grafana health...")
        
        base_url = self.base_urls[self.environment]["grafana"]
        
        try:
            # Health check
            response = requests.get(f"{base_url}/api/health", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "Grafana health check failed"))
                return False
            
            # Test datasources
            response = requests.get(f"{base_url}/api/datasources", timeout=10)
            if response.status_code == 200:
                datasources = response.json()
                prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]
                if not prometheus_ds:
                    self.results.append(("WARN", "No Prometheus datasource configured in Grafana"))
            
            # Test dashboards
            response = requests.get(f"{base_url}/api/search", timeout=10)
            if response.status_code == 200:
                dashboards = response.json()
                if len(dashboards) == 0:
                    self.results.append(("WARN", "No dashboards found in Grafana"))
                else:
                    self.results.append(("PASS", f"Found {len(dashboards)} dashboards in Grafana"))
            
            self.results.append(("PASS", "Grafana health check passed"))
            return True
            
        except requests.RequestException as e:
            self.results.append(("FAIL", f"Grafana connection failed: {e}"))
            return False

    def test_alertmanager_health(self) -> bool:
        """Test AlertManager health and configuration."""
        print("🔍 Testing AlertManager health...")
        
        base_url = self.base_urls[self.environment]["alertmanager"]
        
        try:
            # Health check
            response = requests.get(f"{base_url}/-/healthy", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "AlertManager health check failed"))
                return False
            
            # Ready check
            response = requests.get(f"{base_url}/-/ready", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "AlertManager ready check failed"))
                return False
            
            # Test configuration
            response = requests.get(f"{base_url}/api/v1/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                if "configYAML" in status["data"]:
                    self.results.append(("PASS", "AlertManager configuration loaded"))
                else:
                    self.results.append(("WARN", "AlertManager configuration not found"))
            
            # Test alerts endpoint
            response = requests.get(f"{base_url}/api/v1/alerts", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "AlertManager alerts API failed"))
                return False
            
            self.results.append(("PASS", "AlertManager health check passed"))
            return True
            
        except requests.RequestException as e:
            self.results.append(("FAIL", f"AlertManager connection failed: {e}"))
            return False

    def test_metrics_collection(self) -> bool:
        """Test that application metrics are being collected."""
        print("🔍 Testing metrics collection...")
        
        base_url = self.base_urls[self.environment]["prometheus"]
        
        try:
            # Test for WebSets application metrics
            test_metrics = [
                "http_requests_total",
                "http_request_duration_seconds",
                "db_connections_active",
                "up"
            ]
            
            collected_metrics = 0
            for metric in test_metrics:
                response = requests.get(
                    f"{base_url}/api/v1/query",
                    params={"query": metric},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success" and data["data"]["result"]:
                        collected_metrics += 1
                        self.results.append(("PASS", f"Metric {metric} is being collected"))
                    else:
                        self.results.append(("WARN", f"Metric {metric} not found"))
                else:
                    self.results.append(("WARN", f"Failed to query metric {metric}"))
            
            if collected_metrics == 0:
                self.results.append(("FAIL", "No application metrics are being collected"))
                return False
            elif collected_metrics < len(test_metrics):
                self.results.append(("WARN", f"Only {collected_metrics}/{len(test_metrics)} metrics found"))
            else:
                self.results.append(("PASS", "All expected metrics are being collected"))
            
            return True
            
        except requests.RequestException as e:
            self.results.append(("FAIL", f"Metrics collection test failed: {e}"))
            return False

    def test_alert_rules(self) -> bool:
        """Test that alert rules are loaded and working."""
        print("🔍 Testing alert rules...")
        
        base_url = self.base_urls[self.environment]["prometheus"]
        
        try:
            # Get alert rules
            response = requests.get(f"{base_url}/api/v1/rules", timeout=10)
            if response.status_code != 200:
                self.results.append(("FAIL", "Failed to fetch alert rules"))
                return False
            
            data = response.json()
            if data["status"] != "success":
                self.results.append(("FAIL", "Alert rules API returned error"))
                return False
            
            rule_groups = data["data"]["groups"]
            total_rules = sum(len(group["rules"]) for group in rule_groups)
            
            if total_rules == 0:
                self.results.append(("FAIL", "No alert rules loaded"))
                return False
            
            # Check for WebSets specific rules
            websets_rules = 0
            for group in rule_groups:
                if "websets" in group["name"].lower():
                    websets_rules += len(group["rules"])
            
            if websets_rules == 0:
                self.results.append(("WARN", "No WebSets-specific alert rules found"))
            else:
                self.results.append(("PASS", f"Found {websets_rules} WebSets alert rules"))
            
            self.results.append(("PASS", f"Total {total_rules} alert rules loaded"))
            return True
            
        except requests.RequestException as e:
            self.results.append(("FAIL", f"Alert rules test failed: {e}"))
            return False

    def test_dashboard_queries(self) -> bool:
        """Test that dashboard queries are working."""
        print("🔍 Testing dashboard queries...")
        
        prometheus_url = self.base_urls[self.environment]["prometheus"]
        
        # Sample queries from our dashboards
        test_queries = [
            "sum(rate(http_requests_total[5m]))",
            "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        ]
        
        working_queries = 0
        for query in test_queries:
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        working_queries += 1
                        self.results.append(("PASS", f"Dashboard query working: {query[:50]}..."))
                    else:
                        self.results.append(("WARN", f"Dashboard query failed: {query[:50]}..."))
                else:
                    self.results.append(("WARN", f"Dashboard query HTTP error: {query[:50]}..."))
                    
            except requests.RequestException:
                self.results.append(("WARN", f"Dashboard query connection error: {query[:50]}..."))
        
        if working_queries == 0:
            self.results.append(("FAIL", "No dashboard queries are working"))
            return False
        elif working_queries < len(test_queries):
            self.results.append(("WARN", f"Only {working_queries}/{len(test_queries)} dashboard queries working"))
        else:
            self.results.append(("PASS", "All dashboard queries are working"))
        
        return True

    def run_tests(self) -> bool:
        """Run all smoke tests."""
        print(f"🚀 Running monitoring smoke tests for {self.environment} environment...\n")
        
        tests = [
            self.test_prometheus_health,
            self.test_grafana_health,
            self.test_alertmanager_health,
            self.test_metrics_collection,
            self.test_alert_rules,
            self.test_dashboard_queries,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.results.append(("FAIL", f"Test {test.__name__} crashed: {e}"))
                failed += 1
            print()
        
        # Print results
        print("📊 Test Results:")
        for status, message in self.results:
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[status]
            print(f"   {icon} {message}")
        
        print(f"\n📈 Summary: {passed} passed, {failed} failed")
        
        success = failed == 0
        if success:
            print("✅ All monitoring smoke tests passed!")
        else:
            print("❌ Some monitoring smoke tests failed!")
        
        return success


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run monitoring smoke tests")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        default="staging",
        help="Environment to test"
    )
    
    args = parser.parse_args()
    
    tester = MonitoringSmokeTests(args.environment)
    success = tester.run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

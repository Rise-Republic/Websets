# Tenant Lifecycle Runbook

This runbook describes how to provision new tenants, adjust configuration, and decommission old tenants. A helper script `scripts/tenant_lifecycle.py` automates these tasks.

## Provisioning
1. Run the script with the admin credentials for the new tenant:
   ```bash
   python scripts/tenant_lifecycle.py provision --email admin@example.com --password "ChangeMe!"
   ```
2. The command prints a generated tenant UUID. Store this ID securely as it is required for future operations.

## Configuration
Use the script to modify retention settings or other per-tenant values:
```bash
python scripts/tenant_lifecycle.py configure --tenant-id <TENANT_ID> --retention-days 180
```
This updates users, jobs, and datasets belonging to the tenant.

## Decommissioning
When a tenant leaves the service, purge their data:
```bash
python scripts/tenant_lifecycle.py decommission --tenant-id <TENANT_ID>
```
All users, jobs, datasets, discovery records, crawl results and access logs tied to the tenant are removed. Ensure backups and exports have been handled prior to running this command.

# Backups and Disaster Recovery

Regular database backups ensure Websets can be recovered after a failure. Use the
[`scripts/backup_db.sh`](../../scripts/backup_db.sh) helper to dump PostgreSQL.

## Regular Backups

1. Schedule a cron job on the database host:
   ```bash
   /path/to/repo/scripts/backup_db.sh /backups/webset_miner-$(date +%F).sql
   ```
2. Copy backups to off‑site storage with versioning enabled.

## Disaster Recovery

1. Stop application containers to prevent new writes.
2. Restore the latest dump:
   ```bash
   docker exec -i websets-db-1 psql -U postgres -d webset_miner < backup.sql
   ```
3. Restart services and verify application health.

See also [Secret Rotation Guide](../SECRET_ROTATION.md) for rotating credentials before restoring backups.

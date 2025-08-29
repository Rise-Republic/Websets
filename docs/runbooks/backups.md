# Backups and Disaster Recovery

Regular database backups ensure Websets can be recovered after a failure. Use the
[`scripts/backup_db.sh`](../../scripts/backup_db.sh) helper to dump PostgreSQL and
[`scripts/restore_db.sh`](../../scripts/restore_db.sh) to load a dump back into a
running database.

## Regular Backups

1. Schedule a cron job on the database host:
   ```bash
   /path/to/repo/scripts/backup_db.sh /backups/webset_miner-$(date +%F).sql
   ```
2. Copy backups to off‑site storage with versioning enabled.

## Disaster Recovery

1. Stop application containers to prevent new writes.
2. Restore the latest dump using the helper script:
   ```bash
   ./scripts/restore_db.sh backup.sql
   ```
3. Restart services and verify application health.

## Automated Disaster Recovery Drill

An automated GitHub Actions workflow performs a weekly backup and restore drill
in a disposable environment. The workflow
[`dr-drill.yml`](../../.github/workflows/dr-drill.yml) spins up the stack,
executes `scripts/backup_db.sh` and `scripts/restore_db.sh`, and checks the
application's `/v1/health` endpoint to ensure recovery succeeds. Trigger it
manually from the **Actions** tab to run the drill on demand.

See also [Secret Rotation Guide](../SECRET_ROTATION.md) for rotating credentials before restoring backups.

#!/usr/bin/env python3
"""Manage tenant lifecycle operations.

Examples:
  python scripts/tenant_lifecycle.py provision --email admin@example.com --password Secret123
  python scripts/tenant_lifecycle.py configure --tenant-id <uuid> --retention-days 90
  python scripts/tenant_lifecycle.py decommission --tenant-id <uuid>
"""

import argparse
import sys
import uuid
from loguru import logger
from pathlib import Path

# Ensure app modules are on the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import (
    User,
    Job,
    Dataset,
    DataRecord,
    DiscoveredURL,
    CrawlResult,
    DataAccessLog,
)
from app.auth.jwt_handler import get_password_hash


def provision(args: argparse.Namespace) -> None:
    """Create a tenant and admin user."""
    db = SessionLocal()
    try:
        tenant_id = uuid.uuid4()
        user = User(
            email=args.email,
            hashed_password=get_password_hash(args.password),
            full_name=args.full_name or args.email,
            is_active=True,
            is_admin=True,
            tenant_id=tenant_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Provisioned tenant %s", tenant_id)
        logger.info("Created admin user %s", user.email)
    finally:
        db.close()


def configure(args: argparse.Namespace) -> None:
    """Update tenant configuration (currently retention settings)."""
    db = SessionLocal()
    try:
        tid = uuid.UUID(args.tenant_id)
        db.query(Job).filter(Job.tenant_id == tid).update(
            {Job.data_retention_days: args.retention_days}
        )
        db.query(Dataset).filter(Dataset.tenant_id == tid).update(
            {Dataset.data_retention_days: args.retention_days}
        )
        db.query(User).filter(User.tenant_id == tid).update(
            {User.data_retention_days: args.retention_days}
        )
        db.commit()
        logger.info("Updated retention for tenant %s", tid)
    finally:
        db.close()


def decommission(args: argparse.Namespace) -> None:
    """Delete all data associated with a tenant."""
    db = SessionLocal()
    try:
        tid = uuid.UUID(args.tenant_id)
        db.query(DataAccessLog).filter(DataAccessLog.tenant_id == tid).delete()
        db.query(CrawlResult).filter(CrawlResult.tenant_id == tid).delete()
        db.query(DiscoveredURL).filter(DiscoveredURL.tenant_id == tid).delete()
        db.query(DataRecord).filter(DataRecord.tenant_id == tid).delete()
        db.query(Dataset).filter(Dataset.tenant_id == tid).delete()
        db.query(Job).filter(Job.tenant_id == tid).delete()
        db.query(User).filter(User.tenant_id == tid).delete()
        db.commit()
        logger.info("Decommissioned tenant %s", tid)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tenant lifecycle automation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prov = sub.add_parser("provision", help="Create a tenant and admin user")
    p_prov.add_argument("--email", required=True, help="Admin email")
    p_prov.add_argument("--password", required=True, help="Admin password")
    p_prov.add_argument("--full-name", help="Admin full name")

    p_conf = sub.add_parser("configure", help="Configure an existing tenant")
    p_conf.add_argument("--tenant-id", required=True, help="Tenant UUID")
    p_conf.add_argument(
        "--retention-days",
        type=int,
        default=365,
        help="Data retention period",
    )

    p_decom = sub.add_parser("decommission", help="Remove all tenant data")
    p_decom.add_argument("--tenant-id", required=True, help="Tenant UUID")

    args = parser.parse_args()

    if args.cmd == "provision":
        provision(args)
    elif args.cmd == "configure":
        configure(args)
    else:
        decommission(args)


if __name__ == "__main__":
    main()

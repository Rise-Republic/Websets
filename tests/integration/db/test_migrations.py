import os
import pytest
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command


@pytest.mark.integration
@pytest.mark.slow
def test_run_migrations(tmp_path):
    """Ensure alembic migrations apply cleanly."""
    with PostgresContainer("postgres:13") as pg:
        os.environ["DATABASE_URL"] = pg.get_connection_url()
        os.environ["DB_URL"] = pg.get_connection_url()
        cfg = Config("alembic.ini")
        cfg.set_main_option("script_location", "migrations")
        cfg.set_main_option("sqlalchemy.url", pg.get_connection_url())
        command.upgrade(cfg, "head")

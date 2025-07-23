"""Add indexes for query optimization"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_indexes_20250801'
down_revision = 'add_auth_fields_20250721'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
    op.create_index('ix_datasets_job_id', 'datasets', ['job_id'])
    op.create_index('ix_data_records_dataset_id', 'data_records', ['dataset_id'])
    op.create_index('ix_discovered_urls_job_id', 'discovered_urls', ['job_id'])
    op.create_index('ix_crawl_results_discovered_url_id', 'crawl_results', ['discovered_url_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_data_access_logs_user_id', 'data_access_logs', ['user_id'])
    op.create_index('ix_data_access_logs_dataset_id', 'data_access_logs', ['dataset_id'])
    op.create_index('ix_data_access_logs_job_id', 'data_access_logs', ['job_id'])


def downgrade():
    op.drop_index('ix_data_access_logs_job_id', table_name='data_access_logs')
    op.drop_index('ix_data_access_logs_dataset_id', table_name='data_access_logs')
    op.drop_index('ix_data_access_logs_user_id', table_name='data_access_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_crawl_results_discovered_url_id', table_name='crawl_results')
    op.drop_index('ix_discovered_urls_job_id', table_name='discovered_urls')
    op.drop_index('ix_data_records_dataset_id', table_name='data_records')
    op.drop_index('ix_datasets_job_id', table_name='datasets')
    op.drop_index('ix_jobs_created_at', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_user_id', table_name='jobs')


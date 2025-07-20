-- Initialize WebSet Miner database

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for performance
-- These will be applied after tables are created by SQLAlchemy

-- User table indexes
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Job table indexes  
-- CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
-- CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
-- CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Dataset table indexes
-- CREATE INDEX IF NOT EXISTS idx_datasets_job_id ON datasets(job_id);

-- Data record table indexes
-- CREATE INDEX IF NOT EXISTS idx_data_records_dataset_id ON data_records(dataset_id);
-- CREATE INDEX IF NOT EXISTS idx_data_records_source_url ON data_records(source_url);

-- Discovered URL table indexes
-- CREATE INDEX IF NOT EXISTS idx_discovered_urls_job_id ON discovered_urls(job_id);
-- CREATE INDEX IF NOT EXISTS idx_discovered_urls_url ON discovered_urls(url);
-- CREATE INDEX IF NOT EXISTS idx_discovered_urls_crawled ON discovered_urls(is_crawled);

-- Crawl result table indexes
-- CREATE INDEX IF NOT EXISTS idx_crawl_results_discovered_url_id ON crawl_results(discovered_url_id);
-- CREATE INDEX IF NOT EXISTS idx_crawl_results_success ON crawl_results(success);
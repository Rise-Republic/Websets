# System Architecture

This document describes the overall service layout and the data flow within Websets.

## Service Layout

- **FastAPI API server** – handles user requests and orchestrates background jobs.
- **Celery workers** – execute long running mining tasks.
- **PostgreSQL** – primary relational database for job metadata and extracted datasets.
- **Vector store** – pluggable backend (ChromaDB, Pinecone, Qdrant, or Weaviate) for semantic search.
- **Redis** – message broker and result backend for Celery.
- **Object storage** – MinIO or S3 compatible bucket for raw crawl artifacts.
- **Frontend** – React application that interacts with the API.

## Data Flow

```text
User Prompt → Planner Agent → Discovery Agent → Browser Crawler → Schema Inference → Storage (PostgreSQL + Vector store)
```

1. A user submits a mining prompt through the API or UI.
2. The Planner Agent devises a workflow and schedules jobs via Celery.
3. The Discovery Agent finds relevant URLs which are handed off to the Browser Crawler.
4. Crawled pages are parsed by the Schema Inference Agent to determine data structure.
5. Structured records are stored in PostgreSQL while embeddings are stored in the chosen vector database.

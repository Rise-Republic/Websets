import numpy as np
import pytest
from fastapi import status


@pytest.fixture(autouse=True)
def disable_rbac(monkeypatch):
    from app.middleware.rbac import RBACMiddleware

    async def allow_all(self, request, call_next):
        return await call_next(request)

    monkeypatch.setattr(RBACMiddleware, "dispatch", allow_all)


@pytest.fixture
def tenant_users(create_user):
    return create_user("u1@example.com"), create_user("u2@example.com")


@pytest.fixture
def sample_datasets(db_session, tenant_users):
    from app.models.job import Job
    from app.models.dataset import Dataset, DataRecord

    u1, u2 = tenant_users

    job1 = Job(user_id=u1["user_id"], tenant_id=u1["tenant_id"], prompt="p1")
    job2 = Job(user_id=u2["user_id"], tenant_id=u2["tenant_id"], prompt="p2")
    db_session.add_all([job1, job2])
    db_session.commit()

    ds1 = Dataset(job_id=job1.id, tenant_id=u1["tenant_id"], name="ds1")
    ds2 = Dataset(job_id=job2.id, tenant_id=u2["tenant_id"], name="ds2")
    db_session.add_all([ds1, ds2])
    db_session.commit()

    rec1 = DataRecord(
        dataset_id=ds1.id,
        tenant_id=u1["tenant_id"],
        source_url="http://example.com/1",
        source_title="title1",
        data={"v": 1},
        confidence_score=0.9,
        extraction_method="manual",
    )
    rec2 = DataRecord(
        dataset_id=ds1.id,
        tenant_id=u1["tenant_id"],
        source_url="http://example.com/2",
        source_title="title2",
        data={"v": 2},
        confidence_score=0.8,
        extraction_method="manual",
    )
    rec3 = DataRecord(
        dataset_id=ds2.id,
        tenant_id=u2["tenant_id"],
        source_url="http://example.com/3",
        source_title="title3",
        data={"v": 3},
        confidence_score=0.7,
        extraction_method="manual",
    )
    db_session.add_all([rec1, rec2, rec3])
    db_session.commit()

    return {
        "user1": {"job": job1, "dataset": ds1, "records": [rec1, rec2]},
        "user2": {"job": job2, "dataset": ds2, "records": [rec3]},
    }


@pytest.fixture
def search_stubs(monkeypatch):
    from app.api import datasets as api_datasets

    class DummyStore:
        def __init__(self):
            self.results = []

        def load(self):
            return True

        def search(self, query_vector, k=10, threshold=0.5):
            return self.results

    store = DummyStore()
    monkeypatch.setattr(api_datasets, "VectorStore", lambda: store)
    monkeypatch.setattr(
        api_datasets.EmbeddingGenerator,
        "generate_embedding",
        lambda self, text: np.zeros(2),
    )
    return store


@pytest.mark.integration
class TestDatasetSearch:
    def test_dataset_search_returns_records(self, client, tenant_users, sample_datasets, search_stubs):
        u1, _ = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)
        rec_ids = [str(r.id) for r in sample_datasets["user1"]["records"]]

        search_stubs.results = [
            {"dataset_id": ds1, "record_id": rec_ids[0], "similarity_score": 0.1},
            {"dataset_id": ds1, "record_id": rec_ids[1], "similarity_score": 0.2},
        ]

        resp = client.post(
            f"/datasets/{ds1}/search",
            json={"query": "test"},
            headers=u1["headers"],
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        ids = [r["record"]["id"] for r in data["results"]]
        assert set(ids) == set(rec_ids)
        assert data["total_found"] == 2

    def test_cross_tenant_search_forbidden(self, client, tenant_users, sample_datasets, search_stubs):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)

        search_stubs.results = []

        resp = client.post(
            f"/datasets/{ds1}/search",
            json={"query": "other"},
            headers=u2["headers"],
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

import uuid
import pytest
from fastapi import status


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def keys(self, pattern):
        import fnmatch

        return [k for k in self.store if fnmatch.fnmatch(k, pattern)]

    def delete(self, *keys):
        for k in keys:
            self.store.pop(k, None)


@pytest.fixture(autouse=True)
def disable_rbac(monkeypatch):
    from app.middleware.rbac import RBACMiddleware

    async def allow_all(self, request, call_next):
        return await call_next(request)

    monkeypatch.setattr(RBACMiddleware, "dispatch", allow_all)


@pytest.fixture
def fake_cache(monkeypatch):
    from app.utils import cache

    fake = FakeRedis()
    monkeypatch.setattr(cache, "redis_client", fake)
    return fake


@pytest.fixture
def tenant_users(client, db_session):
    from app.models.user import User

    def create_user(email):
        data = {"email": email, "password": "Passw0rd!", "full_name": email}
        reg = client.post("/auth/register", json=data)
        token = reg.json()["verification_token"]
        client.post("/auth/verify", json={"token": token})
        user = db_session.query(User).filter(User.email == email).first()
        user.tenant_id = uuid.uuid4()
        db_session.commit()
        user_id = str(user.id)
        tenant_id = str(user.tenant_id)

        login = client.post(
            "/auth/login",
            data={"username": email, "password": "Passw0rd!"},
        )
        access = login.json()["access_token"]
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "headers": {"Authorization": f"Bearer {access}"},
        }

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

    rec = DataRecord(
        dataset_id=ds1.id,
        tenant_id=u1["tenant_id"],
        source_url="http://example.com",
        data={"v": 1},
    )
    db_session.add(rec)
    db_session.commit()

    return {
        "user1": {"job": job1, "dataset": ds1},
        "user2": {"job": job2, "dataset": ds2},
    }


@pytest.mark.integration
class TestTenantIsolation:
    def test_dataset_listing_scoped(self, client, tenant_users, sample_datasets):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)
        ds2 = str(sample_datasets["user2"]["dataset"].id)

        r1 = client.get("/datasets/", headers=u1["headers"])
        assert r1.status_code == status.HTTP_200_OK
        ids = [d["id"] for d in r1.json()["datasets"]]
        assert ds1 in ids and ds2 not in ids

        r2 = client.get("/datasets/", headers=u2["headers"])
        assert r2.status_code == status.HTTP_200_OK
        ids = [d["id"] for d in r2.json()["datasets"]]
        assert ds2 in ids and ds1 not in ids

    def test_dataset_detail_isolated(self, client, tenant_users, sample_datasets):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)
        ds2 = str(sample_datasets["user2"]["dataset"].id)

        assert (
            client.get(f"/datasets/{ds2}", headers=u1["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            client.get(f"/datasets/{ds1}", headers=u2["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )

        assert (
            client.get(f"/datasets/{ds1}", headers=u1["headers"]).status_code
            == status.HTTP_200_OK
        )
        assert (
            client.get(f"/datasets/{ds2}", headers=u2["headers"]).status_code
            == status.HTTP_200_OK
        )

    def test_dataset_records_isolated(self, client, tenant_users, sample_datasets):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)

        r = client.get(f"/datasets/{ds1}/records", headers=u1["headers"])
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["total"] == 1

        assert (
            client.get(f"/datasets/{ds1}/records", headers=u2["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )

    def test_job_isolation(self, client, tenant_users, sample_datasets):
        u1, u2 = tenant_users
        job1 = str(sample_datasets["user1"]["job"].id)
        job2 = str(sample_datasets["user2"]["job"].id)

        r1 = client.get("/jobs/", headers=u1["headers"])
        assert r1.status_code == status.HTTP_200_OK
        ids = [j["id"] for j in r1.json()["jobs"]]
        assert job1 in ids and job2 not in ids

        r2 = client.get("/jobs/", headers=u2["headers"])
        assert r2.status_code == status.HTTP_200_OK
        ids = [j["id"] for j in r2.json()["jobs"]]
        assert job2 in ids and job1 not in ids

        assert (
            client.get(f"/jobs/{job2}", headers=u1["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            client.get(f"/jobs/{job1}", headers=u2["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )

        assert (
            client.get(f"/jobs/{job1}", headers=u1["headers"]).status_code
            == status.HTTP_200_OK
        )
        assert (
            client.get(f"/jobs/{job2}", headers=u2["headers"]).status_code
            == status.HTTP_200_OK
        )

    def test_delete_dataset_cross_tenant_denied(
        self, client, tenant_users, sample_datasets
    ):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)

        assert (
            client.delete(f"/datasets/{ds1}", headers=u2["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            client.delete(f"/datasets/{ds1}", headers=u1["headers"]).status_code
            == status.HTTP_200_OK
        )

    def test_dataset_records_cache_isolation(
        self, client, tenant_users, sample_datasets, fake_cache
    ):
        u1, u2 = tenant_users
        ds1 = str(sample_datasets["user1"]["dataset"].id)

        # First request should populate cache
        r = client.get(f"/datasets/{ds1}/records", headers=u1["headers"])
        assert r.status_code == status.HTTP_200_OK

        # Second tenant should not get cached data
        assert (
            client.get(f"/datasets/{ds1}/records", headers=u2["headers"]).status_code
            == status.HTTP_404_NOT_FOUND
        )

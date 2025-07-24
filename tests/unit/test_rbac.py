import pytest
from fastapi import HTTPException

from app.auth import rbac

class DummyPerm:
    def __init__(self, name):
        self.name = name

class DummyRole:
    def __init__(self, name, perms=None):
        self.name = name
        self.permissions = perms or []

class DummyUser:
    def __init__(self, roles, active=True):
        self.roles = roles
        self.is_active = active


@pytest.mark.unit
class TestRBACDependencies:
    def test_require_roles_allows_matching_role(self):
        user = DummyUser([DummyRole("admin")])
        dep = rbac.require_roles("admin")
        assert dep(current_user=user) is user

    def test_require_roles_denies_missing_role(self):
        user = DummyUser([DummyRole("viewer")])
        dep = rbac.require_roles("admin")
        with pytest.raises(HTTPException) as exc:
            dep(current_user=user)
        assert exc.value.status_code == 403

    def test_require_permissions_allows_matching_permission(self):
        perm = DummyPerm("jobs:create")
        user = DummyUser([DummyRole("admin", [perm])])
        dep = rbac.require_permissions("jobs:create")
        assert dep(current_user=user) is user

    def test_require_permissions_denies_missing_permission(self):
        perm = DummyPerm("jobs:read")
        user = DummyUser([DummyRole("viewer", [perm])])
        dep = rbac.require_permissions("jobs:create")
        with pytest.raises(HTTPException) as exc:
            dep(current_user=user)
        assert exc.value.status_code == 403

    def test_require_roles_handles_missing_attribute(self):
        class IncompleteUser:
            pass

        dep = rbac.require_roles("admin")
        with pytest.raises(HTTPException) as exc:
            dep(current_user=IncompleteUser())
        assert exc.value.status_code == 403

    def test_require_roles_handles_none_roles(self):
        user = DummyUser(None)
        dep = rbac.require_roles("admin")
        with pytest.raises(HTTPException) as exc:
            dep(current_user=user)
        assert exc.value.status_code == 403

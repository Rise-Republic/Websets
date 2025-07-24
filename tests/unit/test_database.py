import pytest
from sqlalchemy.orm import Session
from app.database import get_db


@pytest.mark.unit
def test_get_db_yields_session():
    generator = get_db()
    assert hasattr(generator, "__iter__")
    session = next(generator)
    assert isinstance(session, Session)
    session.close()
    with pytest.raises(StopIteration):
        next(generator)

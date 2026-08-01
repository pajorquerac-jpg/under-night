from collections.abc import Generator
from datetime import UTC, datetime, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.models.venue import Venue

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    session.add_all(
        [
            Venue(
                name="Economico Centro",
                zone="Centro",
                latitude=-33.45,
                longitude=-70.66,
                entry_price=Decimal("0"),
                average_drink_price=Decimal("3000"),
                opening_time=time(20, 0),
                closing_time=time(4, 0),
                minimum_age=18,
                music_tags=["pop"],
                ambience_tags=["baile"],
                features={},
                data_updated_at=datetime.now(UTC),
            ),
            Venue(
                name="Premium Oriente",
                zone="Oriente",
                latitude=-33.42,
                longitude=-70.58,
                entry_price=Decimal("25000"),
                average_drink_price=Decimal("9000"),
                opening_time=time(21, 0),
                closing_time=time(5, 0),
                minimum_age=18,
                music_tags=["house"],
                ambience_tags=["premium"],
                features={},
                data_updated_at=datetime.now(UTC),
            ),
        ]
    )
    session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db: Session) -> TestClient:
    return TestClient(app)

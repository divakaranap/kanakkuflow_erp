import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Ensure test DB is SQLite in-memory before config is initialized
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.app.config import settings
settings.DATABASE_URL = "sqlite:///:memory:"

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.user import User, UserRole
from backend.app.services.auth_service import get_password_hash

# Pre-compute demo password hash once for rapid testing
DEMO_PASSWORD_HASH = get_password_hash("demo123")

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_users(db: Session) -> dict:
    users = {
        "owner": User(
            username="owner",
            email="owner@kanakkuflow.com",
            full_name="Owner User",
            role=UserRole.OWNER,
            hashed_password=DEMO_PASSWORD_HASH,
            is_active=True,
        ),
        "admin": User(
            username="admin",
            email="admin@kanakkuflow.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            hashed_password=DEMO_PASSWORD_HASH,
            is_active=True,
        ),
        "salesA": User(
            username="salesA",
            email="salesa@kanakkuflow.com",
            full_name="Sales User A",
            role=UserRole.SALESMAN,
            hashed_password=DEMO_PASSWORD_HASH,
            is_active=True,
        ),
        "prod": User(
            username="prod",
            email="prod@kanakkuflow.com",
            full_name="Production User",
            role=UserRole.PRODUCTION,
            hashed_password=DEMO_PASSWORD_HASH,
            is_active=True,
        ),
        "auditor": User(
            username="auditor",
            email="auditor@kanakkuflow.com",
            full_name="Auditor User",
            role=UserRole.AUDITOR,
            hashed_password=DEMO_PASSWORD_HASH,
            is_active=True,
        ),
    }
    for u in users.values():
        db.add(u)
    db.commit()
    for u in users.values():
        db.refresh(u)
    return users

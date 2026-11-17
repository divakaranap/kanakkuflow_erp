"""Seed script for FACTORYFLOW demo accounts and baseline data."""
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine
from backend.app.models.base import Base
from backend.app.models.user import User, UserRole
from backend.app.services.auth_service import get_password_hash


DEMO_USERS = [
    {
        "username": "owner",
        "email": "owner@kanakkuflow.local",
        "full_name": "Senthil Kumar (Factory Owner)",
        "role": UserRole.OWNER,
        "password": "demo123",
    },
    {
        "username": "admin",
        "email": "admin@kanakkuflow.local",
        "full_name": "Ramesh Swaminathan (Admin Manager)",
        "role": UserRole.ADMIN,
        "password": "demo123",
    },
    {
        "username": "salesA",
        "email": "salesa@kanakkuflow.local",
        "full_name": "Karthik Raja (Sales Executive TN)",
        "role": UserRole.SALESMAN,
        "password": "demo123",
    },
    {
        "username": "salesB",
        "email": "salesb@kanakkuflow.local",
        "full_name": "Anand Prakash (Sales Executive KA)",
        "role": UserRole.SALESMAN,
        "password": "demo123",
    },
    {
        "username": "prod",
        "email": "prod@kanakkuflow.local",
        "full_name": "Muthu Vel (Production Supervisor)",
        "role": UserRole.PRODUCTION,
        "password": "demo123",
    },
    {
        "username": "auditor",
        "email": "auditor@kanakkuflow.local",
        "full_name": "Venkatesh CA (Chartered Accountant)",
        "role": UserRole.AUDITOR,
        "password": "demo123",
    },
]


def seed_users(db: Session) -> None:
    print("-> Seeding default demo users...")
    for user_data in DEMO_USERS:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                hashed_password=get_password_hash(user_data["password"]),
                is_active=True,
            )
            db.add(user)
            print(f"   [+] Created user: {user.username} ({user.role.value})")
        else:
            print(f"   [*] User already exists: {existing.username} ({existing.role.value})")
    db.commit()
    print("-> Demo users seeded successfully.")


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

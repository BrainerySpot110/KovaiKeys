import sys
from database import SessionLocal, Base, engine
from models import User

Base.metadata.create_all(bind=engine)


def create_admin(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.role = "Admin"
            db.commit()
            print(f"Existing user {email} promoted to Admin.")
            return

        admin = User(name=name, email=email, password=password, role="Admin")
        db.add(admin)
        db.commit()
        print(f"Admin account created for {email}.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Usage: python create_admin.py "Full Name" email password')
        sys.exit(1)

    create_admin(sys.argv[1], sys.argv[2], sys.argv[3])

"""
Create (or reset) an admin account.

Usage:
    python create_admin.py
    python create_admin.py --email admin@samunnathi.org --name "Admin" --password "..."

If an admin with the given email already exists, its password is reset
instead of creating a duplicate.
"""
import argparse
import getpass
import sys

from app import create_app
from models import db
from models.user import Admin


def main():
    parser = argparse.ArgumentParser(description="Create or reset a Samunnathi admin account.")
    parser.add_argument("--name", help="Admin display name")
    parser.add_argument("--email", help="Admin login email")
    parser.add_argument("--password", help="Admin password (omit to be prompted securely)")
    args = parser.parse_args()

    name = args.name or input("Admin name: ").strip()
    email = (args.email or input("Admin email: ").strip()).lower()
    password = args.password or getpass.getpass("Admin password (min 8 chars): ")

    if not name or not email or len(password) < 8:
        print("Name, email, and an 8+ character password are all required.")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        db.create_all()
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            admin.set_password(password)
            admin.name = name
            db.session.commit()
            print(f"Existing admin '{email}' updated with a new password.")
        else:
            admin = Admin(name=name, email=email)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account created: {email}")


if __name__ == "__main__":
    main()

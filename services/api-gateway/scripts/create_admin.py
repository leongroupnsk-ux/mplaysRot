"""One-shot script: creates an admin user if not already exists."""
import asyncio, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def main(email: str, password: str, full_name: str = "Admin") -> None:
    from app.db.postgres import AsyncSessionLocal
    from app.models.user import User
    from app.utils.jwt import hash_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        user = existing.scalar_one_or_none()
        if user:
            user.password_hash = hash_password(password)
            user.role = "owner"
            user.is_active = True
            await db.commit()
            print(f"✓ Updated existing user: {email}")
        else:
            db.add(User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role="owner",
            ))
            await db.commit()
            print(f"✓ Created admin user: {email}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "password"
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Admin"
    asyncio.run(main(email, password, full_name))

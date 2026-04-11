import asyncio
import os
import sys
from uuid import uuid4

# Add the backend directory to sys.path so we can import from app
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from sqlalchemy import select
from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models.user import User

async def create_superadmin():
    email = "superadmin@hospitalbilling.com"  # Change this to your preferred email
    password = "SuperSecure123"               # Change this to your preferred password
    full_name = "System Super Admin"

    async with async_session_factory() as db:
        # Check if already exists
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Superadmin with email {email} already exists.")
            return

        # Create superadmin (tenant_id is None)
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="superadmin",
            tenant_id=None,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        print(f"Successfully created Super Admin!")
        print(f"Email: {email}")
        print(f"Password: {password}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_superadmin())

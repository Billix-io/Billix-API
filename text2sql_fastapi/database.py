from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
from config import settings

Base = declarative_base()

# ✅ PostgreSQL Async URL using asyncpg
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

# Create async engine
async_engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
)

# Initialize the DB
async def init_db():
    """
    Initializes the database by creating all tables defined in the models.
    """
    print("⏳ Initializing DB...")
    from models.users import User
    from models.payment import Payment
    from models.user_database import UserDatabase
    from models.roles import Role
    from models.api_usage import ApiUsage
    from models.api_purchase_quota import ApiPurchaseQuota
    from models.plan import Plan
    from models.user_subscription import UserSubscription
    from models.users_api_key import UsersApiKey
    from models.help_and_support import HelpAndSupport
    
 

    # ...import other models here

    async with async_engine.begin() as conn:
        print("📥 Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database created successfully.")

# Dependency to get the DB session
async def get_session() -> AsyncSession:
    """
    Dependency that provides an async database session for FastAPI endpoints.
    """
    async_session = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# CLI run support
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())

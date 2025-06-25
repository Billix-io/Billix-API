import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings

async def reset_database():
    """Drop and recreate the database"""
    # Create engine without database name to connect to postgres
    postgres_url = (
        f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}"
        f"@{settings.database_hostname}:{settings.database_port}/postgres"
    )
    
    engine = create_async_engine(postgres_url, echo=True)
    
    async with engine.begin() as conn:
        # Drop the database if it exists
        await conn.execute(f"DROP DATABASE IF EXISTS {settings.database_name}")
        # Create the database
        await conn.execute(f"CREATE DATABASE {settings.database_name}")
    
    await engine.dispose()
    
    # Now initialize the database with new schema
    from database import init_db
    await init_db()
    
    print("✅ Database reset successfully!")

if __name__ == "__main__":
    asyncio.run(reset_database()) 
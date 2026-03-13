"""
Database Connection and Engine Setup
Provides async SQLAlchemy engine and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path
import os

# Database path
BASE_DIR = Path(__file__).parent.parent

# Use /tmp directory on Vercel (serverless environment)
if os.environ.get('VERCEL'):
    DB_PATH = Path("/tmp/health_data.db")
else:
    DB_PATH = BASE_DIR / "health_data.db"
    
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL query logging
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db():
    """Dependency for FastAPI endpoints to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database connection (call on startup)"""
    # Verify database exists
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            f"Please run: python database/migrate.py"
        )
    
    print(f"✅ Database connected: {DB_PATH}")
    return True

async def close_db():
    """Close database connections (call on shutdown)"""
    await engine.dispose()
    print("🔒 Database connections closed")

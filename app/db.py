from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create schema / tables against Postgres (used by `ingest/run.py --store pg`).

    Runs 'CREATE EXTENSION IF NOT EXISTS vector;' automatically so a manual
    Neon step is not required. Remote-only: the local SqliteStore stand-in
    builds its own schema.
    """
    import app.models  # noqa: F401  (register models on Base)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Schema drift guard: tables created before Phase 2 (or hand-made in the
        # Neon SQL editor) made knowledge_fragments.embedding NOT NULL. Embeddings
        # are optional until the ML stack is installed, so drop the constraint
        # (no-op when the column is already nullable).
        await conn.execute(text("ALTER TABLE knowledge_fragments ALTER COLUMN embedding DROP NOT NULL"))
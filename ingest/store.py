import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.config import settings

LOCAL_SQLITE_PATH = ".zuri_store.sqlite"


class Store(ABC):
    @abstractmethod
    async def get_hash(self, source_key: str) -> str | None: ...

    @abstractmethod
    async def replace_source(
        self, *, source_key: str, title: str, topic: str, doc_type: str, content_hash: str,
        chunks: list[str], embeddings: list[list[float] | None] | None, source_url: str | None,
    ) -> str: ...

    async def ensure_schema(self) -> None:
        """Create/verify tables & extension. No-op by default (SqliteStore
        builds its schema in connect())."""

    async def reset(self) -> None:
        """Drop stored knowledge content (not part of default flow; --reset flag)."""

    @abstractmethod
    async def close(self) -> None: ...


class PgVectorStore(Store):
    """PostgreSQL + pgvector backend (production path).

    Reuses the app ORM (app.models) and the async engine from app.db.
    `source_key` is stored in the knowledge_documents.source_url column
    (values like 'url::https://...' or 'file::C:/...').
    """

    def __init__(self):
        from app.db import SessionLocal, engine
        from app.models import KnowledgeDocument, KnowledgeFragment  # noqa: F401

        self._SessionLocal = SessionLocal
        self._engine = engine
        self._KnowledgeDocument = KnowledgeDocument
        self._KnowledgeFragment = KnowledgeFragment

    async def get_hash(self, source_key: str) -> str | None:
        from sqlalchemy import select

        async with self._SessionLocal() as session:
            result = await session.execute(
                select(self._KnowledgeDocument.content_hash).where(
                    self._KnowledgeDocument.source_url == source_key
                )
            )
            return result.scalar_one_or_none()

    async def ensure_schema(self) -> None:
        from app.db import init_models

        await init_models()

    async def reset(self) -> None:
        """Drop all knowledge content (documents + fragments only)."""
        from sqlalchemy import delete

        async with self._SessionLocal() as session:
            await session.execute(delete(self._KnowledgeDocument))
            await session.execute(delete(self._KnowledgeFragment))
            await session.commit()

    async def replace_source(self, *, source_key, title, topic, doc_type, content_hash,
                             chunks, embeddings, source_url) -> str:
        from sqlalchemy import select

        embeddings = embeddings or [None] * len(chunks)
        now = datetime.now(timezone.utc)

        async with self._SessionLocal() as session:
            result = await session.execute(
                select(self._KnowledgeDocument).where(
                    self._KnowledgeDocument.source_url == source_key
                )
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                await session.delete(existing)
                status = "updated"
            else:
                status = "new"

            document = self._KnowledgeDocument(
                source_url=source_key,
                title=title,
                doc_type=doc_type,
                content_hash=content_hash,
                last_fetched=now,
            )
            session.add(document)
            await session.flush()

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                session.add(
                    self._KnowledgeFragment(
                        document_id=document.id,
                        chunk_index=i,
                        content=chunk,
                        embedding=embedding,
                        source_url=source_url,
                        topic=topic,
                        last_fetched=now,
                    )
                )
            await session.commit()
            return status

    async def close(self) -> None:
        await self._engine.dispose()


class SqliteStore(Store):
    """Local SQLite stand-in for development when the Neon endpoint is
    unreachable (e.g. networks that block outbound :5432). Never used in
    production; embeddings are stored as JSON so vector search is computed
    in-process during Phase 4 retrievals."""

    def __init__(self, path: str = LOCAL_SQLITE_PATH):
        self._path = path
        self._db = None

    async def connect(self) -> None:
        import aiosqlite

        self._db = await aiosqlite.connect(self._path)
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                source_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                last_fetched TEXT NOT NULL
            )
            """
        )
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_key TEXT NOT NULL REFERENCES documents(source_key) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                topic TEXT,
                embedding_json TEXT
            )
            """
        )
        await self._db.commit()

    async def get_hash(self, source_key: str) -> str | None:
        cursor = await self._db.execute(
            "SELECT content_hash FROM documents WHERE source_key = ?", (source_key,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else None

    async def replace_source(self, *, source_key, title, topic, doc_type, content_hash,
                             chunks, embeddings, source_url) -> str:
        embeddings = embeddings or [None] * len(chunks)
        cursor = await self._db.execute(
            "SELECT 1 FROM documents WHERE source_key = ?", (source_key,)
        )
        existing = await cursor.fetchone()
        await cursor.close()
        status = "updated" if existing else "new"
        if existing:
            await self._db.execute("DELETE FROM documents WHERE source_key = ?", (source_key,))

        await self._db.execute(
            """INSERT INTO documents (source_key, title, topic, doc_type, content_hash, last_fetched)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_key, title, topic, doc_type, content_hash, datetime.now(timezone.utc).isoformat()),
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            await self._db.execute(
                """INSERT INTO fragments
                   (source_key, chunk_index, content, source_url, topic, embedding_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    source_key,
                    i,
                    chunk,
                    source_url,
                    topic,
                    json.dumps(embedding) if embedding is not None else None,
                ),
            )
        await self._db.commit()
        return status

    async def reset(self) -> None:
        await self._db.execute("DELETE FROM documents")
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()


async def resolve_store(store_type: str | None = None) -> Store:
    """'auto' (default): PgVectorStore when DATABASE_URL is set, else SqliteStore.
    'pg' / 'sqlite' force a backend."""
    import os

    if store_type is None:
        store_type = os.environ.get("INGEST_STORE", "auto")

    has_database_url = settings.database_url and not settings.database_url.startswith(
        "postgresql+asyncpg://localhost"
    )
    if store_type == "pg" or (store_type == "auto" and has_database_url):
        return PgVectorStore()

    if store_type in {"sqlite", "auto"}:
        store = SqliteStore()
        await store.connect()
        return store

    raise ValueError(f"Unknown store type: {store_type}")
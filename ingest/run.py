"""Full ingestion pipeline lands in Phase 2.

Expected flow:
  local PDFs/DOCX + KQ FAQ web pages
    -> parse (pypdf / python-docx / trafilatura)
    -> clean
    -> fixed-size chunk with overlap + metadata tags (source_url, topic, timestamp)
    -> embed (bge-small-en-v1.5, CPU)
    -> upsert into pgvector (KnowledgeDocument / KnowledgeFragment)
"""

import argparse


def run(sources: list[str] | None = None) -> None:
    raise NotImplementedError("Phase 2: ingestion pipeline")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into the vector store")
    parser.add_argument("--source", action="append", help="Extra source URL or file path")
    args = parser.parse_args()
    run(args.source)
"""Stale-data refresh lands in Phase 2.

Strategy (from the plan):
  - Re-fetch each known source, compute its SHA-256 content hash, and compare
    against KnowledgeDocument.content_hash.
  - Only changed sources are re-chunked / re-embedded (delete fragments for the
    source, reinsert), leaving unchanged sources untouched.
  - Local PDFs refresh manually by re-running this script after a file update.
"""

import argparse


def refresh() -> None:
    raise NotImplementedError("Phase 2: hash-based refresh")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh changed knowledge sources")
    args = parser.parse_args()
    refresh()
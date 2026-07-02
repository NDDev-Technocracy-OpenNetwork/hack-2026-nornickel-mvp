"""Batch-ingest a real document corpus directory into the ledger.

Runs inside the api container (no HTTP hop), file by file, with per-file
size caps and quarantine-over-crash semantics:

    docker compose -f docker-compose.server.yml exec -T api \
        python scripts/ingest_corpus.py --dir data/corpus --limit 60

Unsupported formats (.zip/.rar/.doc/.pptx/.xls) are counted and skipped —
extending them is a documented P2, not a silent failure.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

SUPPORTED = {".pdf", ".docx", ".csv", ".md", ".markdown", ".txt"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="Corpus directory (recursed)")
    parser.add_argument("--limit", type=int, default=0, help="Max files to ingest (0 = all)")
    parser.add_argument("--max-mb", type=float, default=20.0, help="Per-file size cap")
    args = parser.parse_args()

    from nornikel_kg.services.runtime import get_ingestion_service

    service = get_ingestion_service()
    service.synchronous_enrichment = True  # batch runs want completed statuses

    stats = {"completed": 0, "quarantined": 0, "failed": 0, "skipped": 0, "too_large": 0}
    started = time.time()
    files = sorted(
        path for path in Path(args.dir).rglob("*") if path.is_file()
    )
    ingested = 0
    for path in files:
        if args.limit and ingested >= args.limit:
            break
        if path.suffix.lower() not in SUPPORTED:
            stats["skipped"] += 1
            continue
        size_mb = path.stat().st_size / 1024 / 1024
        if size_mb > args.max_mb:
            stats["too_large"] += 1
            print(f"TOO_LARGE ({size_mb:.0f}MB) {path.name[:70]}")
            continue
        ingested += 1
        file_started = time.time()
        try:
            response = service.ingest_upload(
                filename=path.name, content=path.read_bytes()
            )
            status = response.source.status
            stats[status if status in stats else "completed"] = (
                stats.get(status if status in stats else "completed", 0) + 1
            )
            print(
                f"{status.upper():<12} {time.time() - file_started:5.1f}s "
                f"{response.evidence_count:4d} spans  {path.name[:70]}"
            )
        except Exception as error:  # single bad file must never stop the batch
            stats["failed"] += 1
            print(f"FAILED       {path.name[:70]}: {error!r}")
    elapsed = time.time() - started
    print(
        f"\nDone in {elapsed:.0f}s: {stats} "
        f"({ingested} ingested of {len(files)} files seen)"
    )


if __name__ == "__main__":
    main()

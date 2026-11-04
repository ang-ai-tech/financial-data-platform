"""Command line entry point: `findata <command>`."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from findata import db, pipeline
from findata.config import load_settings


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="findata", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create the raw schema and tables (idempotent)")

    ingest = sub.add_parser("ingest", help="Incremental load from the public sources")
    ingest.add_argument("--source", choices=["ecb", "fred", "all"], default="all")
    ingest.add_argument("--start", type=date.fromisoformat, help="Override start date")
    ingest.add_argument("--full-refresh", action="store_true",
                        help="Reload everything from FINDATA_START_DATE")

    export = sub.add_parser("export-sample", help="Write a CSV snapshot for CI/offline use")
    export.add_argument("--out", type=Path, default=Path("data/sample"))
    export.add_argument("--start", type=date.fromisoformat, default=date(2023, 1, 1))

    load_sample = sub.add_parser("load-sample", help="Load the CSV snapshot into raw")
    load_sample.add_argument("--dir", type=Path, default=Path("data/sample"))

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = _parse_args(argv)
    settings = load_settings()

    if args.command == "export-sample":
        pipeline.export_sample(settings, args.out, args.start)
        return

    with db.connect() as conn:
        db.init_schema(conn)
        if args.command == "ingest":
            batch_id = pipeline.new_batch_id()
            options = {"batch_id": batch_id, "start": args.start, "full_refresh": args.full_refresh}
            if args.source in ("ecb", "all"):
                pipeline.ingest_ecb(settings, conn, **options)
            if args.source in ("fred", "all"):
                pipeline.ingest_fred(settings, conn, **options)
        elif args.command == "load-sample":
            rows = pipeline.load_sample(settings, conn, args.dir)
            logging.info("Loaded %d sample rows", rows)


if __name__ == "__main__":
    main()

import time
from typing import Tuple

from db import SessionLocal
from models import titles
from fetch_metadata import fetch_and_parse_omdb


def update_all_ratings(batch_sleep_seconds: float = 0.2, commit_every: int = 100, dry_run: bool = False) -> Tuple[int, int]:
    """Update `imdb_rating` for all rows with an `imdb_id`.

    Returns (updated_count, failed_count).
    """
    db = SessionLocal()
    stmt = titles.select().where(titles.c.imdb_id != None)
    rows = db.execute(stmt).fetchall()

    updated = 0
    failed = 0

    for idx, row in enumerate(rows, start=1):
        imdb_id = row.imdb_id
        if not imdb_id:
            continue

        meta = fetch_and_parse_omdb(imdb_id)
        if not meta:
            print(f"❌ Failed to fetch OMDb for {imdb_id}")
            failed += 1
            time.sleep(batch_sleep_seconds)
            continue

        imdb_rating = meta.get("imdb_rating")
        try:
            if imdb_rating is not None:
                imdb_rating = float(imdb_rating)
        except Exception:
            imdb_rating = None

        if dry_run:
            print(f"DRY: {imdb_id} -> {imdb_rating}")
        else:
            try:
                db.execute(
                    titles.update()
                    .where(titles.c.imdb_id == imdb_id)
                    .values(imdb_rating=imdb_rating)
                )
                updated += 1
            except Exception as e:
                print(f"❌ DB update failed for {imdb_id}: {e}")
                failed += 1

        if commit_every and (idx % commit_every == 0):
            db.commit()
            print(f"💾 Committed batch at {idx} rows.")

        time.sleep(batch_sleep_seconds)

    if not dry_run:
        db.commit()
    db.close()

    print(f"\nDone. Updated: {updated}, Failed: {failed}")
    return updated, failed


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Update imdb_rating for all titles using OMDb")
    parser.add_argument("--sleep", type=float, dest="batch_sleep_seconds", default=0.2, help="delay between OMDb requests")
    parser.add_argument("--commit-every", type=int, default=100, help="commit every N updates (0 = never)")
    parser.add_argument("--dry-run", action="store_true", help="only fetch ratings and print, do not write to DB")

    args = parser.parse_args()

    updated, failed = update_all_ratings(
        batch_sleep_seconds=args.batch_sleep_seconds,
        commit_every=args.commit_every,
        dry_run=args.dry_run,
    )

    if updated or failed:
        sys.exit(0)

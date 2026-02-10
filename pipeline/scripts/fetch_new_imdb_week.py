import time
from typing import List

from db import SessionLocal
from models import titles
from meta_utils import fetch_and_parse_omdb
from fetch_new_imdb_month import fetch_imdb_ids_for_recent_month


def fetch_new_imdb_week(days: int = 7, min_votes: int = 250, min_rating: float = 5.8, batch_sleep_seconds: float = 0.2, commit_every: int = 100) -> List[str]:
    """Find IMDb IDs released within the last `days` days and insert metadata.

    Returns the list of inserted IMDb IDs.
    """
    ids = fetch_imdb_ids_for_recent_month(days=days, min_votes=min_votes, min_rating=min_rating)
    print(f"📅 Found {len(ids)} candidate IMDb ids released in the last {days} days")

    db = SessionLocal()
    inserted_ids: List[str] = []
    updated = 0
    failed = 0

    for idx, imdb_id in enumerate(ids, start=1):
        # Skip already existing
        existing = db.execute(titles.select().where(titles.c.imdb_id == imdb_id)).fetchone()
        if existing:
            print(f"↩ Skipping {imdb_id} — already in DB (id={existing.id})")
            continue

        print(f"📡 ({idx}/{len(ids)}) Fetching metadata for {imdb_id}")
        meta = fetch_and_parse_omdb(imdb_id)
        if not meta:
            print(f"❌ Failed to fetch OMDb for {imdb_id}")
            failed += 1
            time.sleep(batch_sleep_seconds)
            continue

        insert_stmt = titles.insert().values(
            imdb_id=imdb_id,
            title=meta.get("title"),
            year=meta.get("year"),
            type=meta.get("type"),
            genres=meta.get("genres"),
            plot=meta.get("plot"),
            directors=meta.get("directors"),
            writers=meta.get("writers"),
            producers=meta.get("producers"),
            poster_url=meta.get("poster_url"),
            imdb_rating=meta.get("imdb_rating"),
            release_date=meta.get("release_date"),
            actors=meta.get("actors"),
        )

        try:
            db.execute(insert_stmt)
            inserted_ids.append(imdb_id)
            updated += 1
            print(f"   ✔ Inserted {imdb_id}")
        except Exception as e:
            print(f"❌ DB insert failed for {imdb_id}: {e}")
            failed += 1

        if commit_every and (idx % commit_every == 0):
            db.commit()
            print(f"💾 Committed batch at {idx} rows.")

        time.sleep(batch_sleep_seconds)

    db.commit()
    db.close()

    print("\n🎉 Week import complete!")
    print(f"   ✅ Inserted: {updated}")
    print(f"   ❌ Failed:  {failed}")

    return inserted_ids


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Find recent IMDb IDs (week) and insert metadata")
    parser.add_argument("--days", type=int, default=7, help="how many days back to search (default: 7)")
    parser.add_argument("--min-votes", type=int, default=250, help="minimum number of votes filter")
    parser.add_argument("--min-rating", type=float, default=5.8, help="minimum IMDb rating filter")
    parser.add_argument("--sleep", type=float, dest="batch_sleep_seconds", default=0.2, help="delay between OMDb requests")
    parser.add_argument("--commit-every", type=int, default=100, help="commit every N inserts (0 = never)")
    parser.add_argument("--dry-run", action="store_true", help="only list candidate IMDb ids, do not write to DB")

    args = parser.parse_args()

    if args.dry_run:
        ids = fetch_imdb_ids_for_recent_month(days=args.days, min_votes=args.min_votes, min_rating=args.min_rating)
        print(f"Dry run: found {len(ids)} candidate ids (first 50): {ids[:50]}")
        sys.exit(0)

    inserted = fetch_new_imdb_week(
        days=args.days,
        min_votes=args.min_votes,
        min_rating=args.min_rating,
        batch_sleep_seconds=args.batch_sleep_seconds,
        commit_every=args.commit_every,
    )

    if inserted:
        print(f"Inserted {len(inserted)} new titles")
        sys.exit(0)
    else:
        print("No new titles inserted")
        sys.exit(0)

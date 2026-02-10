import gzip
import time
import requests
from datetime import date, timedelta
from typing import List

from db import SessionLocal
from models import titles
from fetch_metadata import fetch_and_parse_omdb

BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"


def download_file(url: str, filename: str) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)


def load_tsv(filename: str):
    with gzip.open(filename, "rt", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        for line in f:
            yield dict(zip(header, line.strip().split("\t")))


def fetch_imdb_ids_for_recent_month(days: int = 30, min_votes: int = 250, min_rating: float = 6.0) -> List[str]:
    """Return IMDb ids for titles released within the last `days` days.

    Strategy mirrors the monthly script: download IMDb basics + ratings datasets,
    shortlist by rating thresholds, then confirm `Released` via OMDb.
    """
    download_file(BASICS_URL, "basics.tsv.gz")
    download_file(RATINGS_URL, "ratings.tsv.gz")

    valid_rating_ids = set()
    for row in load_tsv("ratings.tsv.gz"):
        num_votes_raw = row.get("numVotes", "\\N")
        rating_raw = row.get("averageRating", "\\N")

        if num_votes_raw == "\\N" or rating_raw == "\\N":
            continue

        try:
            num_votes = int(num_votes_raw)
            rating = float(rating_raw)
        except ValueError:
            continue

        if num_votes >= min_votes and rating >= min_rating:
            valid_rating_ids.add(row["tconst"])

    cutoff = date.today() - timedelta(days=days)
    ids: List[str] = []

    for row in load_tsv("basics.tsv.gz"):
        if row["titleType"] not in ["movie", "tvSeries", "tvMiniSeries"]:
            continue

        imdb_id = row["tconst"]
        if imdb_id not in valid_rating_ids:
            continue

        # Query OMDb to get the Released field and parse full date
        data = fetch_omdb_metadata(imdb_id) if 'fetch_omdb_metadata' in globals() else None
        # fetch_metadata exposes fetch_omdb_metadata via import in that module; try calling it through fetch_metadata
        if data is None:
            try:
                # fallback: call the helper in fetch_metadata module
                from fetch_metadata import fetch_omdb_metadata as _fm
                data = _fm(imdb_id)
            except Exception:
                data = None

        if not data:
            continue

        released = data.get("Released")
        # parse_release_date is provided by fetch_metadata; use it via import
        rd = None
        try:
            from fetch_metadata import parse_release_date as _pr
            rd = _pr(released)
        except Exception:
            rd = None

        if not rd:
            continue

        if rd >= cutoff:
            ids.append(imdb_id)

    return ids


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

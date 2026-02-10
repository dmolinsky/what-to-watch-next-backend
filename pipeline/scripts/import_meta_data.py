import os
import sys
import time
from typing import List

from dotenv import load_dotenv

from db import SessionLocal
from models import titles
from fetch_metadata import fetch_and_parse_omdb

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def insert_title_if_missing(db, imdb_id: str) -> str:
    existing = db.execute(
        titles.select().where(titles.c.imdb_id == imdb_id)
    ).fetchone()

    if existing:
        print(f"↩ Skipping {imdb_id}, already in DB (id={existing.id})")
        return "skipped"

    meta = fetch_and_parse_omdb(imdb_id)
    if not meta:
        print(f"❌ No OMDb data for {imdb_id}")
        return "failed"

    title_name = meta.get("title")
    year = meta.get("year")
    plot = meta.get("plot")
    type_value = meta.get("type")

    # release_date is expected to be a datetime.date or datetime.datetime
    release_obj = meta.get("release_date")
    release_iso = release_obj.isoformat() if release_obj else None

    genres_list = meta.get("genres")
    directors_list = meta.get("directors")
    writers_list = meta.get("writers")
    producers_list = meta.get("producers")
    imdb_rating = meta.get("imdb_rating")
    actors_2 = meta.get("actors")
    poster_url = meta.get("poster_url")

    insert_stmt = titles.insert().values(
        imdb_id=imdb_id,
        title=title_name,
        year=year,
        release_date=release_iso,
        plot=plot,
        type=type_value,
        genres=genres_list or None,
        directors=directors_list or None,
        writers=writers_list or None,
        producers=producers_list or None,
        imdb_rating=imdb_rating,
        actors=actors_2,
        poster_url=poster_url,
    )

    db.execute(insert_stmt)
    print(f"✔ Inserted {imdb_id} - {title_name}")
    return "inserted"


def import_imdb_ids(
    imdb_ids: List[str],
    batch_sleep_seconds: float = 0.2,
) -> None:
    print(f"🧾 Got {len(imdb_ids)} IMDb ids to process")

    db = SessionLocal()

    inserted = 0
    skipped = 0
    failed = 0

    for idx, imdb_id in enumerate(imdb_ids, start=1):
        print(f"\n({idx}/{len(imdb_ids)}) Processing {imdb_id}")
        result = insert_title_if_missing(db, imdb_id)

        if result == "inserted":
            inserted += 1
        elif result == "skipped":
            skipped += 1
        else:
            failed += 1

        if batch_sleep_seconds:
            time.sleep(batch_sleep_seconds)

    db.commit()
    db.close()

    print("\n🎉 Import complete!")
    print(f"   ✅ Inserted: {inserted}")
    print(f"   ↩ Skipped (already in DB): {skipped}")
    print(f"   ❌ Failed: {failed}")


if __name__ == "__main__":
    # Example usage:
    #   python import_imdb_ids.py tt0111161 tt0068646 tt0468569
    if len(sys.argv) < 2:
        print("Usage: python import_imdb_ids.py <imdb_id_1> <imdb_id_2> ...")
        sys.exit(1)

    ids_from_cli = sys.argv[1:]
    import_imdb_ids(ids_from_cli)

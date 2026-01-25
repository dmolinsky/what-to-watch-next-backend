import os
import sys
import time
from typing import List, Optional

import requests
from dotenv import load_dotenv

from db import SessionLocal
from models import titles
from fetch_new_imdb_year import fetch_imdb_ids_for_year

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def fetch_omdb_data(imdb_id: str) -> Optional[dict]:
    """Fetch metadata for a given IMDb ID from the OMDb API."""
    if not OMDB_API_KEY:
        raise RuntimeError("OMDB_API_KEY is missing. Check your .env")

    url = f"https://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"

    try:
        response = requests.get(url, timeout=15)
        data = response.json()
    except Exception as e:
        print(f"❌ Request failed for {imdb_id}: {e}")
        return None

    if data.get("Response") == "False":
        print(f"❌ OMDb Error for {imdb_id}: {data.get('Error')}")
        return None

    return data


def parse_list_field(value: Optional[str]) -> list[str]:
    """
    Converts OMDb comma-separated string fields into a list.
    Example: "John Doe, Jane Smith" → ["John Doe", "Jane Smith"]
    """
    if not value or value == "N/A":
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_imdb_rating(value: Optional[str]) -> Optional[float]:
    """Convert OMDb 'imdbRating' to float, handle missing or 'N/A'."""
    if not value or value == "N/A":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_first_two_actors(value: Optional[str]) -> Optional[list[str]]:
    """Extract the first two actors from OMDb 'Actors' field."""
    if not value or value == "N/A":
        return None

    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        return None

    return parts[:2]


def normalize_poster_url(value: Optional[str]) -> Optional[str]:
    """Return a usable poster URL or None."""
    if not value or value == "N/A":
        return None
    return value


def insert_title_if_missing(db, imdb_id: str) -> str:
    existing = db.execute(
        titles.select().where(titles.c.imdb_id == imdb_id)
    ).fetchone()

    if existing:
        print(f"↩ Skipping {imdb_id}, already in DB (id={existing.id})")
        return "skipped"

    data = fetch_omdb_data(imdb_id)
    if not data:
        print(f"❌ No OMDb data for {imdb_id}")
        return "failed"

    title_name = data.get("Title") or None
    year_raw = data.get("Year") or None
    year: Optional[int] = None
    if year_raw and year_raw.isdigit():
        year = int(year_raw)

    plot = data.get("Plot") or None
    type_value = data.get("Type") or None

    genres_list = parse_list_field(data.get("Genre"))
    directors_list = parse_list_field(data.get("Director"))
    writers_list = parse_list_field(data.get("Writer"))
    producers_list = parse_list_field(data.get("Production"))

    imdb_rating = parse_imdb_rating(data.get("imdbRating"))
    actors_2 = parse_first_two_actors(data.get("Actors"))
    poster_url = normalize_poster_url(data.get("Poster"))

    insert_stmt = titles.insert().values(
        imdb_id=imdb_id,
        title=title_name,
        year=year,
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


def import_year(
        year: int,
        batch_sleep_seconds: float = 0.2,
) -> None:
    imdb_ids: List[str] = fetch_imdb_ids_for_year(year)
    print(f"📅 Year {year}: Found {len(imdb_ids)} IMDb ids")

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
    if len(sys.argv) < 2:
        print("Usage: python import_imdb_year.py 2024")
        sys.exit(1)

    year_arg = int(sys.argv[1])
    import_year(year_arg)

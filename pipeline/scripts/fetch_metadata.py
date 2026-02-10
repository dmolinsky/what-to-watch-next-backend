import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

import requests

from db import SessionLocal
from models import titles

load_dotenv()


OMDB_URL = "http://www.omdbapi.com/"


def fetch_omdb_metadata(imdb_id: str, retries: int = 3, backoff: float = 0.5) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        raise RuntimeError("OMDB_API_KEY not set in environment")

    params = {"i": imdb_id, "apikey": api_key, "r": "json", "plot": "full"}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(OMDB_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("Response") == "True":
                return data
            else:
                return None
        except Exception:
            if attempt < retries:
                time.sleep(backoff * attempt)
                continue
            return None


def parse_release_date(released_value: Optional[str]):
    if not released_value:
        return None
    if released_value == "N/A":
        return None
    try:
        return datetime.strptime(released_value, "%d %b %Y").date()
    except Exception:
        return None


def _to_list(field: Optional[str]) -> List[str]:
    if not field or field == "N/A":
        return []
    return [s.strip() for s in field.split(",") if s.strip()]


def fetch_and_parse_omdb(imdb_id: str) -> Optional[Dict[str, Any]]:
    raw = fetch_omdb_metadata(imdb_id)
    if not raw:
        return None

    title = raw.get("Title")
    year_raw = raw.get("Year")
    try:
        year = int(year_raw.split("–")[0]) if year_raw and year_raw != "N/A" else None
    except Exception:
        year = None

    imdb_rating = raw.get("imdbRating")
    try:
        imdb_rating = float(imdb_rating) if imdb_rating and imdb_rating != "N/A" else None
    except Exception:
        imdb_rating = None

    return {
        "title": title,
        "year": year,
        "type": raw.get("Type"),
        "genres": _to_list(raw.get("Genre")),
        "plot": raw.get("Plot") if raw.get("Plot") != "N/A" else None,
        "directors": _to_list(raw.get("Director")),
        "writers": _to_list(raw.get("Writer")),
        "producers": _to_list(raw.get("Production")),
        "poster_url": raw.get("Poster") if raw.get("Poster") != "N/A" else None,
        "imdb_rating": imdb_rating,
        "release_date": parse_release_date(raw.get("Released")),
        "actors": _to_list(raw.get("Actors")),
        "raw": raw,
    }


def fetch_and_update_metadata(batch_sleep_seconds: float = 0.2, commit_every: int = 200):
    """Fetch full OMDb metadata for titles missing key fields and update DB.

    Updates columns present in `titles` model: `title`, `year`, `type`,
    `genres`, `plot`, `directors`, `writers`, `producers`, `poster_url`,
    `imdb_rating`, `release_date`, `actors`.
    """
    db = SessionLocal()

    # Select rows that are missing any important metadata
    result = db.execute(
        titles.select().where(
            (titles.c.imdb_id != None)
            & (
                (titles.c.plot == None)
                | (titles.c.directors == None)
                | (titles.c.writers == None)
                | (titles.c.producers == None)
                | (titles.c.genres == None)
                | (titles.c.poster_url == None)
                | (titles.c.imdb_rating == None)
                | (titles.c.release_date == None)
                | (titles.c.actors == None)
            )
        )
    ).fetchall()

    print(f"🔍 Found {len(result)} titles that need OMDb metadata.")

    updated = 0
    failed = 0

    for idx, row in enumerate(result, start=1):
        imdb_id = row.imdb_id
        title = row.title

        print(f"📡 ({idx}/{len(result)}) Fetching OMDb for {imdb_id} - {title}")

        meta = fetch_and_parse_omdb(imdb_id)
        if not meta:
            print(f"❌ No OMDb data found for {imdb_id}")
            failed += 1
            time.sleep(batch_sleep_seconds)
            continue

        vals = {
            "title": meta.get("title") or row.title,
            "year": meta.get("year") or row.year,
            "type": meta.get("type") or row.type,
            "genres": meta.get("genres") or row.genres,
            "plot": meta.get("plot") or row.plot,
            "directors": meta.get("directors") or row.directors,
            "writers": meta.get("writers") or row.writers,
            "producers": meta.get("producers") or row.producers,
            "poster_url": meta.get("poster_url") or row.poster_url,
            "imdb_rating": meta.get("imdb_rating") or row.imdb_rating,
            "release_date": meta.get("release_date") or row.release_date,
            "actors": meta.get("actors") or row.actors,
        }

        update_stmt = (
            titles.update()
            .where(titles.c.id == row.id)
            .values(**vals)
        )

        db.execute(update_stmt)
        updated += 1
        print(f"   ✔ Updated: {imdb_id}")

        if commit_every and (idx % commit_every == 0):
            db.commit()
            print(f"💾 Committed batch at {idx} rows.")

        time.sleep(batch_sleep_seconds)

    db.commit()
    db.close()

    print("\n🎉 Metadata update complete!")
    print(f"   ✅ Updated: {updated}")
    print(f"   ❌ Failed:  {failed}")


if __name__ == "__main__":
    fetch_and_update_metadata()

import time
from dotenv import load_dotenv

from db import SessionLocal
from models import titles
from meta_utils import fetch_and_parse_omdb

load_dotenv()


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

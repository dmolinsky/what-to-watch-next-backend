# fetch_youtube_batch.py
#
# Fetches YouTube moments-vibes for up to BATCH_SIZE titles per run.
# Safe for YouTube API quota: ~101 units per title.
# Run once per day until all titles have YouTube vibes.

from db import SessionLocal
from sqlalchemy import text
from fetch_youtube_vibes import fetch_youtube_vibes
import time

BATCH_SIZE = 100  # safe daily limit


def fetch_batch():
    db = SessionLocal()

    # 1. Select titles that have NO YouTube raw text yet
    rows = db.execute(text("""
        SELECT id, title
        FROM titles
        WHERE id NOT IN (
            SELECT title_id FROM vibe_raw WHERE source = 'youtube'
        )
        LIMIT :limit
    """), {"limit": BATCH_SIZE}).fetchall()

    total = len(rows)
    print(f"\n📦 Starting YouTube batch fetch ({total} titles)\n")

    if total == 0:
        print("🎉 No titles left to fetch!")
        db.close()
        return

    for index, row in enumerate(rows, start=1):
        print(f"\n▶ [{index}/{total}] Fetching: {row.title} (ID {row.id})")

        # 2. Fetch vibe text
        try:
            raw_text = fetch_youtube_vibes(row.title)

            # Very short text → probably useless → treat as empty
            if len(raw_text.strip()) < 50:
                print("⚠️ Very little text returned — skipping storing.")
                continue

            # 3. Save into vibe_raw
            db.execute(text("""
                INSERT INTO vibe_raw (title_id, source, raw_text, processed)
                VALUES (:id, 'youtube', :txt, FALSE)
            """), {"id": row.id, "txt": raw_text})

            db.commit()
            print("✅ Saved")

        except Exception as e:
            print(f"❌ Error fetching {row.title}: {e}")
            # YouTube API sometimes throttles — small sleep helps
            time.sleep(2)

        # gentle pacing (optional)
        time.sleep(0.3)

    db.close()
    print("\n🎉 Batch complete!\n")


if __name__ == "__main__":
    fetch_batch()

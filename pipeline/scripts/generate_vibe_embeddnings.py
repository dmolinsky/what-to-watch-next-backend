from db import SessionLocal
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
import numpy as np

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def normalize(vec):
    """Ensure embedding is unit-normalized (required for cosine distance)."""
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm > 0 else arr.tolist()


def get_latest_raw_text(db, title_id: int, source: str):
    """Fetch the most recent raw text from vibe_raw for YouTube or Reddit."""
    row = db.execute(
        text("""
            SELECT raw_text
            FROM vibe_raw
            WHERE title_id = :id AND source = :source
            ORDER BY fetched_at DESC
            LIMIT 1
        """),
        {"id": title_id, "source": source}
    ).fetchone()

    if row:
        raw = row[0]
        if raw and raw.strip():
            return raw

    return None


def embed_text(text_block: str):
    """Convert raw text -> normalized MiniLM embedding."""
    vec = model.encode(text_block)
    return normalize(vec)


def save_embedding(db, title_id: int, column: str, embedding):
    """Write embedding into the correct column in embeddings table."""

    # Ensure row exists in embeddings
    db.execute(
        text("""
            INSERT INTO embeddings (title_id)
            VALUES (:id)
            ON CONFLICT (title_id) DO NOTHING
        """),
        {"id": title_id}
    )

    # Update embedding column
    db.execute(
        text(f"UPDATE embeddings SET {column} = :emb WHERE title_id = :id"),
        {"emb": embedding, "id": title_id},
    )

    db.commit()


def generate_vibe_embeddings():
    db = SessionLocal()

    # Fetch all titles
    title_rows = db.execute(
        text("SELECT id, title FROM titles")
    ).fetchall()

    for title_id, title_name in title_rows:
        print(f"\n🎨 Generating vibe embeddings for: {title_name} (ID {title_id})")

        # ---- YouTube ----
        youtube_text = get_latest_raw_text(db, title_id, "youtube")

        if youtube_text:
            yt_emb = embed_text(youtube_text)
            save_embedding(db, title_id, "youtube_embedding", yt_emb)
            print("   ✔ YouTube embedding saved")
        else:
            print("   ⚠ No YouTube raw text found")

    db.close()
    print("\n🎉 All vibe embeddings generated!")


if __name__ == "__main__":
    generate_vibe_embeddings()

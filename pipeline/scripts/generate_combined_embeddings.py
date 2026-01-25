# generate_combined_embeddings.py
#
# Combines plot + YouTube embeddings into a final normalized vector.
# Reddit is currently disabled (weight = 0.0).
# Saves result to embeddings.combined_embedding.

from db import SessionLocal
from sqlalchemy import text
import numpy as np
import json

# Weight configuration
PLOT_WEIGHT    = 0.7
YOUTUBE_WEIGHT = 0.3
REDDIT_WEIGHT  = 0.0   # Disabled for now

VECTOR_DIM = 384


def to_vector(vec):
    """Convert DB value (pgvector or JSON) into a numpy float vector."""
    if vec is None:
        return np.zeros(VECTOR_DIM)

    # If stored as JSON string
    if isinstance(vec, str):
        try:
            vec = json.loads(vec)
        except json.JSONDecodeError:
            print("⚠️ JSON decode error, returning zero-vector")
            return np.zeros(VECTOR_DIM)

    arr = np.array(vec, dtype=float)

    # Ensure correct dimension
    if arr.shape[0] != VECTOR_DIM:
        print(f"⚠️ Wrong dimensionality ({arr.shape[0]}) — expected {VECTOR_DIM}. Using zero-vector.")
        return np.zeros(VECTOR_DIM)

    return arr


def normalize(vec):
    """Normalize combined embedding."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()


def combine_vectors(plot_vec, yt_vec, reddit_vec):
    """Weighted linear combination of available vectors."""

    plot = to_vector(plot_vec)
    yt   = to_vector(yt_vec)
    rd   = to_vector(reddit_vec)

    # If youtube missing → fallback to only plot
    if yt_vec is None:
        yt = np.zeros(VECTOR_DIM)

    combined = (
            PLOT_WEIGHT    * plot +
            YOUTUBE_WEIGHT * yt +
            REDDIT_WEIGHT  * rd
    )

    return normalize(combined)


def generate_combined_embeddings():
    db = SessionLocal()

    rows = db.execute(text("""
        SELECT 
            title_id,
            plot_embedding,
            youtube_embedding,
            reddit_embedding
        FROM embeddings
    """)).fetchall()

    print(f"🔍 Found {len(rows)} embedding rows to combine.\n")

    for row in rows:
        if row.plot_embedding is None:
            print(f"⚠️ Skipping {row.title_id}: missing plot embedding.")
            continue

        final_emb = combine_vectors(
            row.plot_embedding,
            row.youtube_embedding,
            row.reddit_embedding
        )

        # Sanity check
        if len(final_emb) != VECTOR_DIM:
            print(f"❌ ERROR: Combined embedding has wrong dimension for {row.title_id}. Skipping.")
            continue

        db.execute(
            text("""
                UPDATE embeddings 
                SET combined_embedding = :vec 
                WHERE title_id = :id
            """),
            {"vec": final_emb, "id": row.title_id}
        )
        db.commit()

        print(f"✅ Combined embedding saved for title {row.title_id}")

    db.close()
    print("\n🎉 All combined embeddings generated!")


if __name__ == "__main__":
    generate_combined_embeddings()

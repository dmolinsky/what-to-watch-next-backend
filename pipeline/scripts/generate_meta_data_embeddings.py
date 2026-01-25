from sqlalchemy import select, text
from db import SessionLocal
from models import titles
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def normalize(vec):
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm > 0 else arr.tolist()


def build_embedding_text(row):
    year = row.year or ""
    type_ = row.type or ""
    genres = ", ".join(row.genres) if row.genres else ""
    plot = row.plot or ""

    return (
        f"A {type_} from {year} in the genres {genres}. "
        f"Plot: {plot}"
    ).strip()


def generate_all_embeddings():
    db = SessionLocal()

    rows = db.execute(select(titles)).fetchall()
    print(f"📝 Titles found: {len(rows)}")

    for row in rows:
        text_content = build_embedding_text(row)

        vector = model.encode(text_content)
        vector = normalize(vector)

        sql = text("""
            INSERT INTO embeddings (title_id, plot_embedding)
            VALUES (:id, :vec)
            ON CONFLICT (title_id)
            DO UPDATE SET plot_embedding = EXCLUDED.plot_embedding
        """)

        db.execute(sql, {"id": row.id, "vec": vector})

        print(f"✨ Saved plot embedding for: {row.title}")

    db.commit()
    db.close()
    print("🎉 Plot embedding generation complete!")


if __name__ == "__main__":
    generate_all_embeddings()

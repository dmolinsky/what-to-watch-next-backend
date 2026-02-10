from sqlalchemy import Table, Column, Integer, Text, ARRAY, ForeignKey, Float, Date
from sqlalchemy.orm import registry
from pgvector.sqlalchemy import Vector
from db import metadata

mapper_registry = registry()

titles = Table(
    "titles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("imdb_id", Text, unique=True),
    Column("title", Text, nullable=False),
    Column("year", Integer),
    Column("type", Text),
    Column("genres", ARRAY(Text)),
    Column("plot", Text),
    Column("directors", ARRAY(Text)),
    Column("writers", ARRAY(Text)),
    Column("producers", ARRAY(Text)),
    Column("poster_url", Text),
    Column("imdb_rating", Float),
    Column("actors", ARRAY(Text)),
    Column("release_date", Date, nullable=True)
)

embeddings = Table(
    "embeddings",
    metadata,
    Column("title_id", Integer, ForeignKey("titles.id"), primary_key=True),
    Column("plot_embedding", Vector(384)),
    Column("youtube_embedding", Vector(384)),
    Column("reddit_embedding", Vector(384)),
    Column("combined_embedding", Vector(384))
)
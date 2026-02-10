import gzip
import requests
from datetime import date, timedelta
from typing import List

from fetch_metadata import fetch_and_parse_omdb
from import_meta_data import import_imdb_ids  # assumes same folder / import path

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


def fetch_imdb_ids_for_recent_month(
    days: int = 30,
    min_votes: int = 400,
    min_rating: float = 5.8,
) -> List[str]:
    """
    Return IMDb ids for titles released within the last `days` days
    with rating >= min_rating and numVotes >= min_votes.

    Steps:
    - Download IMDb basics + ratings datasets.
    - Filter rating rows by min_votes and min_rating.
    - Join with basics on titleType and tconst.
    - For each candidate, fetch OMDb metadata and use the parsed `release_date`
      from fetch_and_parse_omdb to check exact release date.
    """
    # Download latest IMDb dumps
    download_file(BASICS_URL, "basics.tsv.gz")
    download_file(RATINGS_URL, "ratings.tsv.gz")

    # Filter on rating + votes first (cheaper)
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

    # Walk basics and join with rating filter
    for row in load_tsv("basics.tsv.gz"):
        if row["titleType"] not in ["movie", "tvSeries", "tvMiniSeries"]:
            continue

        imdb_id = row["tconst"]
        if imdb_id not in valid_rating_ids:
            continue

        # Use the same helper as your importer, so release_date parsing is consistent
        meta = fetch_and_parse_omdb(imdb_id)
        if not meta:
            continue

        release_date = meta.get("release_date")
        if not release_date:
            continue

        # release_date is expected to be a datetime.date (or datetime)
        if release_date >= cutoff:
            ids.append(imdb_id)

    return ids


if __name__ == "__main__":
    recent_ids = fetch_imdb_ids_for_recent_month()
    print(f"Found {len(recent_ids)} recent titles:")
    for imdb_id in recent_ids:
        print(imdb_id)

    if recent_ids:
        print("\nImporting metadata for these titles...")
        import_imdb_ids(recent_ids)

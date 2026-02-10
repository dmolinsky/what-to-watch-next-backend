import gzip
import requests
from datetime import date, timedelta
from typing import List

from meta_utils import fetch_omdb_metadata, parse_release_date

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


def fetch_imdb_ids_for_recent_month(days: int = 30, min_votes: int = 250, min_rating: float = 6.0) -> List[str]:
    """Return IMDb ids for titles released within the last `days` days.

    Strategy:
    - Download IMDb basics + ratings datasets.
    - Build a shortlist of candidates by titleType and rating thresholds (for speed).
    - Query OMDb for each candidate and parse `Released` to check exact date.
    """
    download_file(BASICS_URL, "basics.tsv.gz")
    download_file(RATINGS_URL, "ratings.tsv.gz")

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

    for row in load_tsv("basics.tsv.gz"):
        if row["titleType"] not in ["movie", "tvSeries", "tvMiniSeries"]:
            continue

        imdb_id = row["tconst"]
        if imdb_id not in valid_rating_ids:
            continue

        # Query OMDb to get the Released field and parse full date
        data = fetch_omdb_metadata(imdb_id)
        if not data:
            continue

        released = data.get("Released")
        rd = parse_release_date(released)
        if not rd:
            continue

        if rd >= cutoff:
            ids.append(imdb_id)

    return ids


if __name__ == "__main__":
    ids = fetch_imdb_ids_for_recent_month()
    print(f"Found {len(ids)} recent titles:")
    for i in ids:
        print(i)

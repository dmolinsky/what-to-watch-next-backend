import gzip
import sys
import requests

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


def fetch_imdb_ids_for_year(year: int) -> list[str]:
    download_file(BASICS_URL, "basics.tsv.gz")
    download_file(RATINGS_URL, "ratings.tsv.gz")

    rating_ids = set()
    for row in load_tsv("ratings.tsv.gz"):
        num_votes_raw = row.get("numVotes", "\\N")
        if num_votes_raw == "\\N":
            continue
        try:
            num_votes = int(num_votes_raw)
        except ValueError:
            continue

        if num_votes >= 5000:
            rating_ids.add(row["tconst"])

    ids: list[str] = []

    for row in load_tsv("basics.tsv.gz"):
        if row["titleType"] not in ["movie", "tvSeries", "tvMiniSeries"]:
            continue

        if row["startYear"] == "\\N":
            continue

        if int(row["startYear"]) != year:
            continue

        imdb_id = row["tconst"]

        if imdb_id not in rating_ids:
            continue

        ids.append(imdb_id)

    return ids

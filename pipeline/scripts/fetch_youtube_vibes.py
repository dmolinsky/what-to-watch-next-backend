import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build(
    serviceName="youtube",
    version="v3",
    developerKey=YOUTUBE_API_KEY,
    cache_discovery=False
)


SEARCH_QUERIES = [
    "{title} moments",
    "{title} best moments",
    "{title} scenes",
    "{title} highlights",
]


def youtube_search(query: str, max_results=8):
    """Helper that performs a YouTube search and returns video IDs."""
    response = youtube.search().list(
        q=query,
        type="video",
        part="id",
        maxResults=max_results
    ).execute()

    return [item["id"]["videoId"] for item in response.get("items", [])]


def fetch_youtube_vibes(title_name: str) -> str:
    """
    Fetch vibe/"tone" text using YouTube Data API based on:
    - "<title> moments"
    - "<title> scenes"
    - "<title> highlights"
    """

    video_ids = []

    # Try multiple search prompts until we get enough videos
    for template in SEARCH_QUERIES:
        query = template.format(title=title_name)
        print(f"🔍 Searching: {query}")

        ids = youtube_search(query)

        video_ids.extend(ids)

        if len(video_ids) >= 5:
            break

    # Remove duplicates and cap list
    video_ids = list(dict.fromkeys(video_ids))[:8]

    if not video_ids:
        print("⚠️ No videos found!")
        return ""

    # Fetch video metadata
    videos_response = youtube.videos().list(
        part="snippet",
        id=",".join(video_ids)
    ).execute()

    all_text_parts = []

    for item in videos_response.get("items", []):
        snippet = item["snippet"]

        # title, description, tags
        all_text_parts.append(snippet.get("title", ""))
        all_text_parts.append(snippet.get("description", ""))
        all_text_parts.extend(snippet.get("tags", []))

        # Fetch comments
        try:
            comments_response = youtube.commentThreads().list(
                part="snippet",
                videoId=item["id"],
                maxResults=20,
                textFormat="plainText"
            ).execute()

            for c in comments_response.get("items", []):
                comment = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                all_text_parts.append(comment)

        except Exception:
            pass  # comments disabled

    # Combine into one large text block
    combined = " ".join(all_text_parts)
    print(f"📦 Combined text length: {len(combined)} characters")

    return combined

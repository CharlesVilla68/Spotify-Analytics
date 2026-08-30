import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

MAX_RETRIES = 5


def get_top_tags(artist_name):
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "autocorrect": 1,  # lets Last.fm fix minor misspellings/formatting
    }

    attempt = 0
    while attempt < MAX_RETRIES:
        response = requests.get(LASTFM_URL, params=params)

        if response.status_code == 429:
            wait_seconds = 2 ** attempt
            print(f"Rate limited by Last.fm. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            attempt += 1
            continue

        if response.status_code >= 500:
            wait_seconds = 2 ** attempt
            print(f"Last.fm server error ({response.status_code}). Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            attempt += 1
            continue

        response.raise_for_status()
        data = response.json()

        # Last.fm returns errors as HTTP 200 with an "error" field inside
        # the JSON itself, not always as a proper HTTP error status --
        # a quirk worth checking for explicitly.
        if "error" in data:
            return []

        tags = data.get("toptags", {}).get("tag", [])
        return [t["name"] for t in tags]

    raise RuntimeError(f"Gave up after {MAX_RETRIES} retries calling Last.fm for '{artist_name}'")
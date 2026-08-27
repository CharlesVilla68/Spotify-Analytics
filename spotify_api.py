import time
import requests

MAX_RETRIES = 5


def make_spotify_request(method, url, headers, params=None, data=None):
    """
    Makes an HTTP request to Spotify, automatically handling:
    - 429 (rate limited): waits exactly as long as Spotify says, then retries
    - other failures: waits with exponential backoff (1s, 2s, 4s, 8s...), then retries
    Gives up and raises an error after MAX_RETRIES attempts.
    """
    attempt = 0

    while attempt < MAX_RETRIES:
        response = requests.request(method, url, headers=headers, params=params, data=data)

        if response.status_code == 429:
            # Spotify tells us exactly how many seconds to wait,
            # in a header called Retry-After.
            wait_seconds = int(response.headers.get("Retry-After", 1))
            print(f"Rate limited (429). Waiting {wait_seconds}s as instructed by Spotify...")
            time.sleep(wait_seconds)
            attempt += 1
            continue

        if response.status_code >= 500:
            # 500-range = something's wrong on Spotify's end, not ours.
            # Worth retrying with backoff, since it's often temporary.
            wait_seconds = 2 ** attempt  # 1, 2, 4, 8, 16...
            print(f"Spotify server error ({response.status_code}). Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            attempt += 1
            continue

        # Anything else (200 success, or a 4xx that isn't 429, like a
        # genuinely bad request) -- just return/raise normally, no retry.
        response.raise_for_status()
        return response

    raise RuntimeError(f"Gave up after {MAX_RETRIES} retries calling {url}")
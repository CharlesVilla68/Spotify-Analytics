from auth import get_valid_access_token
from spotify_api import make_spotify_request

RECENTLY_PLAYED_URL = "https://api.spotify.com/v1/me/player/recently-played"


def get_recently_played(limit=10):
    access_token = get_valid_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "limit": limit
    }

    response = make_spotify_request("GET", RECENTLY_PLAYED_URL, headers=headers, params=params)
    return response.json()


if __name__ == "__main__":
    data = get_recently_played(limit=10)

    print(f"\nYour last {len(data['items'])} played tracks:\n")
    for item in data["items"]:
        track_name = item["track"]["name"]
        artist_name = item["track"]["artists"][0]["name"]
        played_at = item["played_at"]
        print(f"- {track_name} by {artist_name} (played at {played_at})")
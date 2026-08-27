from auth import get_valid_access_token
from spotify_api import make_spotify_request

TOP_ARTISTS_URL = "https://api.spotify.com/v1/me/top/artists"
TOP_TRACKS_URL = "https://api.spotify.com/v1/me/top/tracks"


def get_top_items(item_type="artists", time_range="medium_term", limit=10):
    access_token = get_valid_access_token()

    url = TOP_ARTISTS_URL if item_type == "artists" else TOP_TRACKS_URL

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "time_range": time_range,
        "limit": limit
    }

    response = make_spotify_request("GET", url, headers=headers, params=params)
    return response.json()


if __name__ == "__main__":
    print("=== Top Artists (last 6 months) ===\n")
    artist_data = get_top_items(item_type="artists", time_range="medium_term", limit=10)
    for i, artist in enumerate(artist_data["items"], start=1):
        artist_genres = artist.get("genres") or []
        genres = ", ".join(artist_genres) if artist_genres else "no genres listed"
        print(f"{i}. {artist['name']} ({genres})")

    print("\n=== Top Tracks (last 6 months) ===\n")
    track_data = get_top_items(item_type="tracks", time_range="medium_term", limit=10)
    for i, track in enumerate(track_data["items"], start=1):
        artist_name = track["artists"][0]["name"]
        print(f"{i}. {track['name']} by {artist_name}")
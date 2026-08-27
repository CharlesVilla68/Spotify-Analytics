import sqlite3
from datetime import date
from get_top_items import get_top_items
from ingest_recently_played import get_or_create_artist, get_or_create_track

DB_FILE = "spotify.db"


def ingest_top_tracks(time_range="medium_term"):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    data = get_top_items(item_type="tracks", time_range=time_range, limit=50)
    items = data["items"]

    snapshot_date = date.today().isoformat()  # e.g. "2026-08-26"

    for rank, track in enumerate(items, start=1):
        artist = track["artists"][0]

        artist_id = get_or_create_artist(
            cursor,
            spotify_artist_id=artist["id"],
            name=artist["name"]
        )

        track_id = get_or_create_track(
            cursor,
            spotify_track_id=track["id"],
            name=track["name"],
            album=track["album"]["name"],
            artist_id=artist_id
        )

        cursor.execute(
            """INSERT INTO top_items_snapshots (track_id, rank, time_range, snapshot_date)
               VALUES (?, ?, ?, ?)""",
            (track_id, rank, time_range, snapshot_date)
        )

    conn.commit()
    conn.close()

    print(f"Saved a {time_range} top-{len(items)}-tracks snapshot, dated {snapshot_date}.")


if __name__ == "__main__":
    ingest_top_tracks(time_range="short_term")
    ingest_top_tracks(time_range="medium_term")
    ingest_top_tracks(time_range="long_term")
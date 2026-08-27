import sqlite3
from get_recently_played import get_recently_played

DB_FILE = "spotify.db"


def get_or_create_artist(cursor, spotify_artist_id, name):
    """
    Looks up an artist by their Spotify ID. If found, returns our
    internal artist_id. If not found, inserts a new row and returns
    the newly created artist_id.
    """
    cursor.execute(
        "SELECT artist_id FROM artists WHERE spotify_artist_id = ?",
        (spotify_artist_id,)
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]  # already exists -- reuse its id

    cursor.execute(
        "INSERT INTO artists (name, spotify_artist_id) VALUES (?, ?)",
        (name, spotify_artist_id)
    )
    return cursor.lastrowid  # id of the row we just created


def get_or_create_track(cursor, spotify_track_id, name, album, artist_id):
    """
    Same 'get or create' pattern, but for tracks. Requires the
    artist_id (our internal id) to already exist, since tracks
    reference artists via foreign key.
    """
    cursor.execute(
        "SELECT track_id FROM tracks WHERE spotify_track_id = ?",
        (spotify_track_id,)
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor.execute(
        "INSERT INTO tracks (name, album, artist_id, spotify_track_id) VALUES (?, ?, ?, ?)",
        (name, album, artist_id, spotify_track_id)
    )
    return cursor.lastrowid


def insert_play(cursor, track_id, played_at):
    """
    Inserts a play event. Uses 'INSERT OR IGNORE' so that if this
    exact played_at timestamp already exists (caught by the UNIQUE
    constraint we added), it silently skips instead of crashing.
    """
    cursor.execute(
        "INSERT OR IGNORE INTO plays (track_id, played_at) VALUES (?, ?)",
        (track_id, played_at)
    )


def ingest_recently_played():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    data = get_recently_played(limit=50)  # max allowed per request
    items = data["items"]

    new_plays = 0

    for item in items:
        track = item["track"]
        artist = track["artists"][0]  # just the primary artist for now
        played_at = item["played_at"]

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

        cursor.execute("SELECT changes()")  # baseline, just for clarity below
        insert_play(cursor, track_id, played_at)
        if cursor.rowcount:
            new_plays += 1

    conn.commit()
    conn.close()

    print(f"Processed {len(items)} recently played tracks from the API.")
    print(f"Inserted {new_plays} new play(s) into the database.")


if __name__ == "__main__":
    ingest_recently_played()
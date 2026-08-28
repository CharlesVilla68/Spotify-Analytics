import sqlite3
import glob
import json

DB_FILE = "spotify.db"
HISTORY_FOLDER = "extended_history"

# Only count a play if you listened for at least this many milliseconds.
# 30,000 ms = 30 seconds. Filters out accidental skips/fast forwards.
MIN_MS_PLAYED = 30000


def get_or_create_artist_by_name(cursor, name):
    cursor.execute(
        "SELECT artist_id FROM artists WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor.execute(
        "INSERT INTO artists (name, spotify_artist_id) VALUES (?, NULL)",
        (name,)
    )
    return cursor.lastrowid


def get_or_create_track_by_spotify_id(cursor, spotify_track_id, name, album, artist_id):
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


def extract_track_id(spotify_track_uri):
    if spotify_track_uri is None:
        return None
    return spotify_track_uri.split(":")[-1]


def ingest_file(cursor, filepath):
    """Processes a single JSON file, returns how many plays were inserted."""
    with open(filepath, "r", encoding="utf-8") as f:
        entries = json.load(f)

    inserted = 0

    for entry in entries:
        track_name = entry.get("master_metadata_track_name")
        artist_name = entry.get("master_metadata_album_artist_name")
        album_name = entry.get("master_metadata_album_album_name")
        spotify_track_uri = entry.get("spotify_track_uri")
        played_at = entry.get("ts")
        ms_played = entry.get("ms_played", 0)

        # Skip podcasts/audiobooks (no track name means it wasn't a song)
        if track_name is None or artist_name is None:
            continue

        # Skip near-instant skips
        if ms_played < MIN_MS_PLAYED:
            continue

        spotify_track_id = extract_track_id(spotify_track_uri)
        if spotify_track_id is None:
            continue

        artist_id = get_or_create_artist_by_name(cursor, artist_name)
        track_id = get_or_create_track_by_spotify_id(
            cursor, spotify_track_id, track_name, album_name, artist_id
        )

        cursor.execute(
            "INSERT OR IGNORE INTO plays (track_id, played_at) VALUES (?, ?)",
            (track_id, played_at)
        )
        if cursor.rowcount:
            inserted += 1

    return inserted


def ingest_extended_history():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Finds every file matching the pattern -- e.g. Streaming_History_Audio_2023_2.json,
    # Streaming_History_Audio_2018.json, etc. Deliberately excludes "_Video_" files.
    pattern = f"{HISTORY_FOLDER}/Streaming_History_Audio_*.json"
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No files found matching {pattern}. Check the folder path.")
        return

    print(f"Found {len(files)} audio history file(s) to process.\n")

    total_inserted = 0

    for filepath in files:
        inserted = ingest_file(cursor, filepath)
        conn.commit()  # save after each file, not after every single row
        total_inserted += inserted
        print(f"{filepath}: inserted {inserted} new play(s)")

    conn.close()

    print(f"\nDone. Total new plays inserted: {total_inserted}")


if __name__ == "__main__":
    ingest_extended_history()
import sqlite3
import time
from lastfm_api import get_top_tags

DB_FILE = "spotify.db"
MAX_TAGS_PER_ARTIST = 5
DELAY_BETWEEN_REQUESTS = 0.25  # seconds -- polite pacing between calls


def artist_already_has_tags(cursor, artist_id):
    cursor.execute(
        "SELECT 1 FROM artist_tags WHERE artist_id = ? LIMIT 1",
        (artist_id,)
    )
    return cursor.fetchone() is not None


def save_tags(cursor, artist_id, tag_names):
    for rank, tag_name in enumerate(tag_names[:MAX_TAGS_PER_ARTIST], start=1):
        cursor.execute(
            "INSERT INTO artist_tags (artist_id, tag_name, tag_rank) VALUES (?, ?, ?)",
            (artist_id, tag_name, rank)
        )


def ingest_artist_tags():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT artist_id, name FROM artists ORDER BY artist_id")
    artists = cursor.fetchall()

    print(f"Found {len(artists)} artists total.\n")

    processed = 0
    skipped = 0

    for artist_id, artist_name in artists:
        if artist_already_has_tags(cursor, artist_id):
            skipped += 1
            continue

        tags = get_top_tags(artist_name)
        save_tags(cursor, artist_id, tags)
        conn.commit()  # commit after each artist -- safe to interrupt anytime

        processed += 1
        if processed % 100 == 0:
            print(f"Processed {processed} artists so far...")

        time.sleep(DELAY_BETWEEN_REQUESTS)

    conn.close()

    print(f"\nDone. Processed {processed} new artist(s), skipped {skipped} already done.")


if __name__ == "__main__":
    ingest_artist_tags()
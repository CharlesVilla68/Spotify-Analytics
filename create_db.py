import sqlite3

DB_FILE = "spotify.db"


def create_database():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spotify_artist_id TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            album TEXT,
            artist_id INTEGER NOT NULL,
            spotify_track_id TEXT UNIQUE,
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)

    # Dropped and recreated with played_at now UNIQUE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            play_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            played_at TEXT NOT NULL UNIQUE,
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS top_items_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            time_range TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artist_tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            tag_rank INTEGER NOT NULL,
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database created (or already existed) at {DB_FILE}")


if __name__ == "__main__":
    create_database()
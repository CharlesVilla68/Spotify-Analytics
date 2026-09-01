import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

DB_FILE = "spotify.db"

app = Flask(__name__)
CORS(app)


def query_db(sql, params=()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Maps a simple preset name to a SQLite date-modifier string.
# 'all' has no filter at all -- meaning "since the beginning."
RANGE_MODIFIERS = {
    "30days": "-30 days",
    "6months": "-6 months",
    "year": "-1 year",
    "all": None,
}


@app.route("/api/top-tracks")
def top_tracks():
    """
    Query parameters (both optional, with defaults):
    - limit: how many results to return (default 10)
    - range: one of "30days", "6months", "year", "all" (default "all")

    Example: GET /api/top-tracks?limit=25&range=year
    """
    limit = request.args.get("limit", default=10, type=int)
    time_range = request.args.get("range", default="all")

    modifier = RANGE_MODIFIERS.get(time_range)

    if modifier is None:
        # "all" (or an unrecognized value) -- no date filter at all
        sql = """
            SELECT
                tracks.name AS track_name,
                artists.name AS artist_name,
                COUNT(*) AS play_count
            FROM plays
            JOIN tracks ON plays.track_id = tracks.track_id
            JOIN artists ON tracks.artist_id = artists.artist_id
            GROUP BY plays.track_id
            ORDER BY play_count DESC
            LIMIT ?
        """
        results = query_db(sql, (limit,))
    else:
        sql = """
            SELECT
                tracks.name AS track_name,
                artists.name AS artist_name,
                COUNT(*) AS play_count
            FROM plays
            JOIN tracks ON plays.track_id = tracks.track_id
            JOIN artists ON tracks.artist_id = artists.artist_id
            WHERE played_at >= date('now', ?)
            GROUP BY plays.track_id
            ORDER BY play_count DESC
            LIMIT ?
        """
        results = query_db(sql, (modifier, limit))

    return jsonify(results)

@app.route("/api/top-genres")
def top_genres():
    """
    Query parameters, same pattern as /api/top-tracks:
    - limit: how many genres to return (default 10)
    - range: one of "30days", "6months", "year", "all" (default "all")

    Example: GET /api/top-genres?limit=15&range=6months
    """
    limit = request.args.get("limit", default=10, type=int)
    time_range = request.args.get("range", default="all")

    modifier = RANGE_MODIFIERS.get(time_range)

    base_select = """
        SELECT
            REPLACE(LOWER(artist_tags.tag_name), '-', ' ') AS genre,
            COUNT(*) AS play_count
        FROM plays
        JOIN tracks ON plays.track_id = tracks.track_id
        JOIN artists ON tracks.artist_id = artists.artist_id
        JOIN artist_tags ON artists.artist_id = artist_tags.artist_id
    """

    if modifier is None:
        sql = base_select + """
            GROUP BY REPLACE(LOWER(artist_tags.tag_name), '-', ' ')
            ORDER BY play_count DESC
            LIMIT ?
        """
        results = query_db(sql, (limit,))
    else:
        sql = base_select + """
            WHERE played_at >= date('now', ?)
            GROUP BY REPLACE(LOWER(artist_tags.tag_name), '-', ' ')
            ORDER BY play_count DESC
            LIMIT ?
        """
        results = query_db(sql, (modifier, limit))

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
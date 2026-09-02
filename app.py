import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

DB_FILE = "spotify.db"

app = Flask(__name__)
CORS(app)

# Only these three units are accepted -- matches SQLite's own date-modifier
# vocabulary, and doubles as a safety allowlist (see build_date_modifier).
VALID_UNITS = {"days", "months", "years"}


def query_db(sql, params=()):
    """
    Runs a SELECT query and returns the results as a list of
    dictionaries, ready to convert into JSON.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_date_modifier():
    """
    Reads 'amount' and 'unit' query parameters and builds a safe
    SQLite date modifier string, e.g. "-5 months".
    Returns None if no real filter should be applied (all-time).
    """
    amount = request.args.get("amount", type=int)
    unit = request.args.get("unit", default="days")

    # No amount given at all, or a non-positive number -- treat as
    # "all time", no filter.
    if amount is None or amount <= 0:
        return None

    # Reject anything not in our allowlist. We're about to build a raw
    # SQL modifier string by combining user input directly (not through
    # a '?' placeholder, since SQLite doesn't allow parameterizing this
    # particular spot), so 'unit' must be restricted to only ever be
    # one of three known-safe words, rather than trusting whatever
    # text arrives from the request.
    if unit not in VALID_UNITS:
        unit = "days"

    return f"-{amount} {unit}"


@app.route("/api/top-tracks")
def top_tracks():
    """
    Query parameters:
    - limit: how many results to return (default 10)
    - amount + unit: e.g. amount=3&unit=months -- omit both for all-time

    Example: GET /api/top-tracks?limit=25&amount=6&unit=months
    """
    limit = request.args.get("limit", default=10, type=int)
    modifier = build_date_modifier()

    if modifier is None:
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
    Same query parameters as /api/top-tracks.
    Example: GET /api/top-genres?limit=15&amount=1&unit=years
    """
    limit = request.args.get("limit", default=10, type=int)
    modifier = build_date_modifier()

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
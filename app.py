import sqlite3
from flask import Flask, jsonify
from flask_cors import CORS

DB_FILE = "spotify.db"

app = Flask(__name__)
CORS(app)  # allows a webpage running separately to call this backend


def query_db(sql, params=()):
    """
    Runs a SELECT query and returns the results as a list of
    dictionaries (e.g. [{"track_name": "12:51", "play_count": 490}, ...])
    instead of plain tuples -- dictionaries are what convert cleanly
    into the JSON format a webpage expects.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.route("/api/top-tracks")
def top_tracks():
    """
    Answers: GET http://127.0.0.1:5000/api/top-tracks
    Returns your top 10 most-played tracks, as JSON.
    """
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
        LIMIT 10
    """
    results = query_db(sql)
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
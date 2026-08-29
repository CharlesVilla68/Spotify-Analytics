import os
import json
import base64
import time
import http.server
import socketserver
import urllib.parse
import webbrowser
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

SCOPES = "user-read-recently-played user-top-read"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOKEN_FILE = "tokens.json"

received_code = {"code": None}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if "code" in query:
            received_code["code"] = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h2>Success! You can close this tab and return to your terminal.</h2>"
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Something went wrong - no code received.</h2>")

    def log_message(self, format, *args):
        pass


def get_authorization_code():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("Opening your browser for Spotify login/approval...")
    webbrowser.open(url)

    with socketserver.TCPServer(("127.0.0.1", 8888), CallbackHandler) as httpd:
        print("Waiting for you to approve access in the browser...")
        httpd.handle_request()

    if received_code["code"] is None:
        raise RuntimeError("Did not receive an authorization code from Spotify.")

    return received_code["code"]


def _basic_auth_header():
    """
    Builds the 'Authorization: Basic ...' header used to prove our
    app's identity to Spotify. Shared by both the initial code
    exchange and the refresh-token exchange, since both need it.
    """
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def exchange_code_for_tokens(auth_code):
    """First-time login: trade an authorization code for tokens."""
    headers = _basic_auth_header()
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token):
    """
    Silent renewal: trade a refresh token for a brand new access
    token, with no browser involved. This is the new piece.
    """
    headers = _basic_auth_header()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def save_tokens(token_data):
    token_data["expires_at"] = time.time() + token_data["expires_in"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"Tokens saved to {TOKEN_FILE}")


def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)


def is_token_expired(token_data):
    return time.time() > token_data["expires_at"]


def get_valid_access_token():
    """
    Main entry point other scripts use.
    1. No saved tokens at all -> full browser login (only path that
       needs a browser).
    2. Saved token still valid -> use it directly.
    3. Saved token expired, but we have a refresh token -> silently
       get a new access token, no browser popup.
    """
    token_data = load_tokens()

    if token_data is not None and not is_token_expired(token_data):
        print("Using saved access token (still valid).")
        return token_data["access_token"]

    if token_data is not None and "refresh_token" in token_data:
        print("Access token expired. Refreshing silently (no browser needed)...")
        new_token_data = refresh_access_token(token_data["refresh_token"])

        # Spotify doesn't always send back a new refresh_token --
        # if it doesn't, keep using the one we already have.
        if "refresh_token" not in new_token_data:
            new_token_data["refresh_token"] = token_data["refresh_token"]

        save_tokens(new_token_data)
        return new_token_data["access_token"]

    print("No saved tokens found. Running login for the first time...")
    code = get_authorization_code()
    token_data = exchange_code_for_tokens(code)
    save_tokens(token_data)
    return token_data["access_token"]


if __name__ == "__main__":
    access_token = get_valid_access_token()
    print(f"\nAccess token ready (first 20 chars): {access_token[:20]}...")
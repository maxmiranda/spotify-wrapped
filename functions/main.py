import time
import requests
from firebase_functions import scheduler_fn
from firebase_admin import initialize_app, firestore

# Initialize Firebase Admin SDK
initialize_app()

# Initialize Firestore client


# Function to refresh the Spotify access token and store tokens in Firestore
def refresh_access_token():
    db = firestore.client()

    # Retrieve refresh token from Firestore
    token_doc = db.collection("tokens").document("auth_tokens").get()
    if not token_doc.exists:
        print("Error: Refresh token not found in Firestore.")
        return False

    tokens = token_doc.to_dict()
    refresh_token = tokens.get("refresh_token")
    client_id = tokens.get("client_id")
    client_secret = tokens.get("client_secret")

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        new_access_token = response.json()["access_token"]
        # Update access token in Firestore
        db.collection("tokens").document("auth_tokens").set(
            {"access_token": new_access_token}, merge=True
        )
        print("Access token refreshed and stored successfully.")
        return new_access_token
    else:
        print(f"Error refreshing token: {response.status_code}, {response.text}")
        return False


# Function to fetch currently playing track or episode
def fetch_currently_playing():
    db = firestore.client()

    # Retrieve access token from Firestore
    token_doc = db.collection("tokens").document("auth_tokens").get()
    if not token_doc.exists:
        print("Error: Access token not found in Firestore.")
        return None

    access_token = token_doc.to_dict().get("access_token")
    url = "https://api.spotify.com/v1/me/player/currently-playing?additional_types=episode"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 204:
        # No track is currently playing
        return None
    elif response.status_code == 401:
        # Token expired, refresh it
        print("Access token expired. Refreshing...")
        new_access_token = refresh_access_token()
        if new_access_token:
            headers["Authorization"] = f"Bearer {new_access_token}"
            response = requests.get(url, headers=headers)
            return response.json() if response.status_code == 200 else None
        else:
            return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


# Function to process track data
def process_track_data(data):
    return {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "track_name": data["item"].get("name", "Unknown"),
        "artists": data["item"].get("artists", [{"name": "Unknown"}]),
        "album_name": data["item"].get("album", {}).get("name", "Unknown"),
        "album_id": data["item"].get("album", {}).get("id", "Unknown"),
        "album_image_url": data["item"]
        .get("album", {})
        .get("images", [{}])[0]
        .get("url", "Unknown"),
        "duration_ms": data["item"].get("duration_ms", 0),
        "progress_ms": data.get("progress_ms", 0),
        "is_playing": data.get("is_playing", False),
        "popularity": data["item"].get("popularity", 0),
        "track_number": data["item"].get("track_number", 0),
        "disc_number": data["item"].get("disc_number", 0),
        "type": "track",
        "spotify_url": data["item"].get("external_urls", {}).get("spotify", "Unknown"),
    }


# Function to process podcast data
def process_podcast_data(data):
    return {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "episode_name": data["item"].get("name", "Unknown"),
        "show_name": data["item"].get("show", {}).get("name", "Unknown"),
        "show_id": data["item"].get("show", {}).get("id", "Unknown"),
        "show_image_url": data["item"]
        .get("show", {})
        .get("images", [{}])[0]
        .get("url", "Unknown"),
        "release_date": data["item"].get("release_date", "Unknown"),
        "description": data["item"].get("description", "Unknown"),
        "duration_ms": data["item"].get("duration_ms", 0),
        "progress_ms": data.get("progress_ms", 0),
        "is_playing": data.get("is_playing", False),
        "type": "episode",
        "spotify_url": data["item"].get("external_urls", {}).get("spotify", "Unknown"),
    }


# Main function triggered by scheduler
@scheduler_fn.on_schedule(schedule="every 1 minutes")
def spotify_polling(event):
    db = firestore.client()
    # Poll Spotify API 5 times with 10-second intervals
    for _ in range(5):
        data = fetch_currently_playing()
        if data:
            if data["currently_playing_type"] == "track":
                document = process_track_data(data)
                db.collection("raw_track_data").add(document)
                print(f"Logged Track: {document}")
            elif data["currently_playing_type"] == "episode":
                document = process_podcast_data(data)
                db.collection("raw_podcast_data").add(document)
                print(f"Logged Podcast: {document}")
        else:
            print("No track or podcast is currently playing.")

        # Wait 10 seconds before the next request
        time.sleep(11)

    print("Finished polling for this minute.")

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import sys
import time

CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'https://example.com/callback'

SCOPE = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative"
)
DEVICE_NAME = "spotifyd-pi"  # Change this to your spotifyd device name

def get_client_id(file_path='/home/pi/.config/spotifyd/CLIENT_ID'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Client ID file '{file_path}' not found.")
        return None

def get_client_secret(file_path='/home/pi/.config/spotifyd/CLIENT_SECRET'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Client ID file '{file_path}' not found.")
        return None

sp_oauth = SpotifyOAuth(client_id=get_client_id(),
                        client_secret=get_client_secret(),
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache",
                        open_browser=False,
                        show_dialog=True)

def get_spotify_client():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        print("Please authenticate with Spotify")
        auth_url = sp_oauth.get_authorize_url()
        print("Open this URL in a browser and paste the URL after login:")
        print(auth_url)
        response = input("Paste redirect URL here: ")
        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    return spotipy.Spotify(auth=token_info['access_token'])


def refresh_token_and_get_spotify():
    token_info = sp_oauth.get_cached_token()
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return spotipy.Spotify(auth=token_info['access_token'])


def get_device_id(sp, device_name=DEVICE_NAME):
    devices = sp.devices()
    for device in devices['devices']:
        if device['name'] == device_name:
            return device['id']
    print(f"Device '{device_name}' not found. Available devices:")
    for device in devices['devices']:
        print(f" - {device['name']}")
    return None


def list_playlists(sp):
    playlists = sp.current_user_playlists()
    print("\nYour Playlists:")
    for i, playlist in enumerate(playlists['items']):
        print(f"{i+1}. {playlist['name']} (Tracks: {playlist['tracks']['total']})")
    return playlists['items']


def play_playlist(sp, device_id, playlist_uri):
    sp.start_playback(device_id=device_id, context_uri=playlist_uri)
    print(f"Playing playlist: {playlist_uri}")


def play_track(sp, device_id, track_uri):
    sp.start_playback(device_id=device_id, uris=[track_uri])
    print(f"Playing track: {track_uri}")


def playback_control(sp, command, device_id):
    try:
        if command == "play":
            sp.start_playback(device_id=device_id)
        elif command == "pause":
            sp.pause_playback(device_id=device_id)
        elif command == "stop":
            sp.pause_playback(device_id=device_id)
        elif command == "toggle":
            playback = sp.current_playback()
            if playback and playback['is_playing']:
                sp.pause_playback(device_id=device_id)
                print("Paused playback.")
            else:
                sp.start_playback(device_id=device_id)
                print("Resumed playback.")
        elif command == "next":
            sp.next_track(device_id=device_id)
            print("Skipped to next track.")
        elif command == "previous":
            sp.previous_track(device_id=device_id)
            print("Went to previous track.")
        elif command == "fast-forward":
            playback = sp.current_playback()
            if playback and playback['progress_ms']:
                new_pos = playback['progress_ms'] + 15000
                duration = playback['item']['duration_ms']
                if new_pos > duration:
                    new_pos = duration - 1000
                sp.seek_track(position_ms=new_pos, device_id=device_id)
                print(f"Fast forwarded 15 seconds to {new_pos} ms.")
        elif command == "rewind":
            playback = sp.current_playback()
            if playback and playback['progress_ms']:
                new_pos = playback['progress_ms'] - 15000
                if new_pos < 0:
                    new_pos = 0
                sp.seek_track(position_ms=new_pos, device_id=device_id)
                print(f"Rewinded 15 seconds to {new_pos} ms.")
        elif command == "volume_up":
            current = sp.current_playback()
            if current:
                vol = current['device']['volume_percent']
                new_vol = min(100, vol + 10)
                sp.volume(new_vol, device_id=device_id)
                print(f"Volume increased to {new_vol}%.")
        elif command == "volume_down":
            current = sp.current_playback()
            if current:
                vol = current['device']['volume_percent']
                new_vol = max(0, vol - 10)
                sp.volume(new_vol, device_id=device_id)
                print(f"Volume decreased to {new_vol}%.")
        elif command == "shuffle_toggle":
            current = sp.current_playback()
            if current:
                shuffle_state = current['shuffle_state']
                sp.shuffle(not shuffle_state, device_id=device_id)
                print(f"Shuffle {'enabled' if not shuffle_state else 'disab-led'}.")
        elif command == "repeat_toggle":
            current = sp.current_playback()
            if current:
                repeat_mode = current['repeat_state']
                new_mode = {"off": "context", "context": "track", "track": "off"}[repeat_mode]
                sp.repeat(new_mode, device_id=device_id)
                print(f"Repeat mode set to {new_mode}.")
        else:
            print("Unknown playback command.")
    except spotipy.exceptions.SpotifyException as e:
        print("Spotify API error:", e)
        print("Try refreshing token and retry.")
        sp = refresh_token_and_get_spotify()
        playback_control(sp, command, device_id)


def print_current_playback(sp):
    playback = sp.current_playback()
    if not playback or not playback['item']:
        print("Nothing is currently playing.")
        return
    item = playback['item']
    artist_names = ", ".join([artist['name'] for artist in item['artists']])
    name = item['name']
    is_playing = playback['is_playing']
    progress = playback['progress_ms'] // 1000
    duration = item['duration_ms'] // 1000
    shuffle = playback['shuffle_state']
    repeat = playback['repeat_state']
    volume = playback['device']['volume_percent']
    print(f"\nCurrently {'Playing' if is_playing else 'Paused'}: {name} by {artist_names}")
    print(f"Progress: {progress}s / {duration}s")
    print(f"Shuffle: {'On' if shuffle else 'Off'}, Repeat: {repeat}, Volume: {volume}%")


def main():
    sp = get_spotify_client()
    device_id = get_device_id(sp)
    if not device_id:
        print("Cannot continue without a Spotify Connect device.")
        sys.exit(1)

    commands = [
        "list_playlists", "play_playlist", "play_track",
        "play", "pause", "stop", "toggle",
        "next", "previous", "fast-forward", "rewind",
        "volume_up", "volume_down", "shuffle_toggle", "repeat_toggle",
        "exit"
    ]
    completer = WordCompleter(commands, ignore_case=True)

    print("Welcome to the Advanced Spotify Controller!")
    while True:
        sp = refresh_token_and_get_spotify()
        print_current_playback(sp)
        user_input = prompt("\nEnter command: ", completer=completer).strip().lower()

        if user_input == "list_playlists":
            list_playlists(sp)
        elif user_input == "play_playlist":
            playlists = list_playlists(sp)
            idx = input("Enter playlist number to play: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(playlists):
                play_playlist(sp, device_id, playlists[int(idx) - 1]['uri'])
            else:
                print("Invalid playlist number.")
        elif user_input == "play_track":
            track_uri = input("Enter Spotify track URI (e.g. spotify:track:...): ").strip()
            play_track(sp, device_id, track_uri)
        elif user_input == "exit":
            print("Exiting controller.")
            break
        elif user_input in commands:
            playback_control(sp, user_input, device_id)
        else:
            print("Unknown command. Try again.")


if __name__ == "__main__":
    main()

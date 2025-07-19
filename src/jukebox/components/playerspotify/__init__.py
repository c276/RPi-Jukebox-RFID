"""
spotify_controller.py

Spotify controller adapted for RPi-Jukebox-RFID integration.
Provides class-based interface for Spotify control (similar to playermpd).
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging

import jukebox.plugs as plugs

logger = logging.getLogger(__name__)

CLIENT_ID_PATH = os.path.expanduser('~/.config/spotifyd/CLIENT_ID')
CLIENT_SECRET_PATH = os.path.expanduser('~/.config/spotifyd/CLIENT_SECRET')
REDIRECT_URI = 'https://example.com/callback'
CACHE_PATH = os.path.expanduser('~/.cache/spotify_controller')

SCOPE = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative"
)

DEVICE_NAME = "spotifyd-pi"


def read_secret(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Error reading secret from {file_path}: {e}")
        return None


class PlayerSpotify:
    def __init__(self):
        self.sp_oauth = SpotifyOAuth(
            client_id=read_secret(CLIENT_ID_PATH),
            client_secret=read_secret(CLIENT_SECRET_PATH),
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=CACHE_PATH,
            open_browser=False,
            show_dialog=True
        )
        self.sp = self.authenticate()
        self.device_id = self.get_device_id()

    def authenticate(self):
        token_info = self.sp_oauth.get_cached_token()
        if not token_info:
            print("\nPlease authenticate Spotify manually:")
            auth_url = self.sp_oauth.get_authorize_url()
            print(f"Open the following URL and paste the redirect URL after login:\n{auth_url}")
            response = input("Paste redirect URL here: ").strip()
            code = self.sp_oauth.parse_response_code(response)
            token_info = self.sp_oauth.get_access_token(code)
        return spotipy.Spotify(auth=token_info['access_token'])

    def refresh(self):
        token_info = self.sp_oauth.get_cached_token()
        if token_info and self.sp_oauth.is_token_expired(token_info):
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
            self.sp = spotipy.Spotify(auth=token_info['access_token'])

    def get_device_id(self):
        self.refresh()
        devices = self.sp.devices().get('devices', [])
        for d in devices:
            if d['name'] == DEVICE_NAME:
                return d['id']
        logger.warning(f"Device '{DEVICE_NAME}' not found.")
        return None

    def play_uri(self, uri):
        self.refresh()
        if uri.startswith('spotify:playlist:'):
            self.sp.start_playback(device_id=self.device_id, context_uri=uri)
        elif uri.startswith('spotify:track:'):
            self.sp.start_playback(device_id=self.device_id, uris=[uri])
        else:
            logger.error(f"Unsupported URI: {uri}")

    def playback_control(self, command):
        self.refresh()
        try:
            if command == "play":
                self.sp.start_playback(device_id=self.device_id)
            elif command in ("pause", "stop"):
                self.sp.pause_playback(device_id=self.device_id)
            elif command == "next":
                self.sp.next_track(device_id=self.device_id)
            elif command == "previous":
                self.sp.previous_track(device_id=self.device_id)
            elif command == "toggle":
                playback = self.sp.current_playback()
                if playback and playback['is_playing']:
                    self.sp.pause_playback(device_id=self.device_id)
                else:
                    self.sp.start_playback(device_id=self.device_id)
            else:
                logger.warning(f"Unknown command: {command}")
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify API error: {e}")

    def volume(self, change):
        self.refresh()
        playback = self.sp.current_playback()
        if playback:
            vol = playback['device']['volume_percent']
            new_vol = max(0, min(100, vol + change))
            self.sp.volume(new_vol, device_id=self.device_id)

    def current_track(self):
        self.refresh()
        playback = self.sp.current_playback()
        if not playback or not playback.get('item'):
            return None
        item = playback['item']
        return {
            'title': item['name'],
            'artist': ', '.join(artist['name'] for artist in item['artists']),
            'is_playing': playback['is_playing'],
            'progress': playback['progress_ms'],
            'duration': item['duration_ms'],
            'volume': playback['device']['volume_percent'],
            'shuffle': playback['shuffle_state'],
            'repeat': playback['repeat_state'],
        }

    def list_playlists(self):
        self.refresh()
        playlists = self.sp.current_user_playlists()
        return [(p['name'], p['uri']) for p in playlists['items']]

    @plugs.tag
    def get_player_type_and_version(self):
        raise NotImplementedError

    @plugs.tag
    def update(self):
        raise NotImplementedError

    @plugs.tag
    def update_wait(self):
        raise NotImplementedError

    @plugs.tag
    def play(self, uri=None):
        if uri:
            self.play_uri(uri)
        else:
            self.play()

    @plugs.tag
    def stop(self):
        raise NotImplementedError

    @plugs.tag
    def pause(self, state: int = 1):
        raise NotImplementedError

    @plugs.tag
    def prev(self):
        raise NotImplementedError

    @plugs.tag
    def next(self):
        raise NotImplementedError

    @plugs.tag
    def seek(self, new_time):
        self.refresh()
        playback = self.sp.current_playback()
        if playback:
            current_pos = playback.get('progress_ms', 0)
            duration = playback['item']['duration_ms']
            new_pos = max(0, min(current_pos + new_time, duration - 1000))
            self.sp.seek_track(position_ms=new_pos, device_id=self.device_id)

    @plugs.tag
    def rewind(self):
        raise NotImplementedError

    @plugs.tag
    def replay(self):
        raise NotImplementedError

    @plugs.tag
    def toggle(self):
        raise NotImplementedError

    @plugs.tag
    def replay_if_stopped(self):
        raise NotImplementedError

    @plugs.tag
    def shuffle(self, option='toggle'):
        self.refresh()
        current = self.sp.current_playback()
        if current:
            state = current.get('shuffle_state', False)
            self.sp.shuffle(not state, device_id=self.device_id)

    @plugs.tag
    def repeat(self, option='toggle'):
        self.refresh()
        current = self.sp.current_playback()
        if current:
            mode = current.get('repeat_state', 'off')
            next_mode = {'off': 'context', 'context': 'track', 'track': 'off'}[mode]
            self.sp.repeat(next_mode, device_id=self.device_id)

    @plugs.tag
    def get_current_song(self, param):
        raise NotImplementedError

    @plugs.tag
    def map_filename_to_playlist_pos(self, filename):
        raise NotImplementedError

    @plugs.tag
    def remove(self):
        raise NotImplementedError

    @plugs.tag
    def move(self):
        raise NotImplementedError

    @plugs.tag
    def play_single(self, song_url):
        raise NotImplementedError

    @plugs.tag
    def resume(self):
        raise NotImplementedError

    @plugs.tag
    def fast_forward(self, seconds: float = 1):
        raise NotImplementedError

    @plugs.tag
    def play_hold_jingle(self, jingle_path: str):
        raise NotImplementedError

    @plugs.tag
    def play_card(self, folder: str, recursive: bool = False):
        raise NotImplementedError

    @plugs.tag
    def get_single_coverart(self, song_url):
        raise NotImplementedError

    @plugs.tag
    def get_album_coverart(self, albumartist: str, album: str):
        raise NotImplementedError

    @plugs.tag
    def flush_coverart_cache(self):
        raise NotImplementedError

    @plugs.tag
    def get_folder_content(self, folder: str):
        raise NotImplementedError

    @plugs.tag
    def play_folder(self, folder: str, recursive: bool = False) -> None:
        raise NotImplementedError

    @plugs.tag
    def play_album(self, albumartist: str, album: str):
        raise NotImplementedError

    @plugs.tag
    def queue_load(self, folder):
        raise NotImplementedError

    @plugs.tag
    def playerstatus(self):
        raise NotImplementedError

    @plugs.tag
    def playlistinfo(self):
        raise NotImplementedError

    @plugs.tag
    def list_all_dirs(self):
        raise NotImplementedError

    @plugs.tag
    def list_albums(self):
        raise NotImplementedError

    @plugs.tag
    def list_songs_by_artist_and_album(self, albumartist, album):
        raise NotImplementedError

    @plugs.tag
    def get_song_by_url(self, song_url):
        raise NotImplementedError

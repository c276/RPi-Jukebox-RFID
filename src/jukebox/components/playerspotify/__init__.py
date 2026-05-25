"""
spotify_controller.py

Spotify controller adapted for RPi-Jukebox-RFID integration.
Provides class-based interface for Spotify control.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
import subprocess
import functools
import time

import jukebox.plugs as plugs
from components.playerhybrid.playcontentcallback import PlayContentCallbacks, PlayCardState
import jukebox.cfghandler
import jukebox.utils as utils
from jukebox.NvManager import nv_manager

logger = logging.getLogger("jb.PlayerSpotify")
cfg = jukebox.cfghandler.get_handler('jukebox')

CLIENT_ID_PATH = os.path.expanduser('~/.config/spotifyd/CLIENT_ID')
CLIENT_SECRET_PATH = os.path.expanduser('~/.config/spotifyd/CLIENT_SECRET')
REDIRECT_URI = 'https://example.com/callback'
CACHE_PATH = os.path.expanduser('~/.cache/spotify_controller')
ERROR_SOUND_PATH = '/home/pi/RPi-Jukebox-RFID/resources/audio/error.wav'
LAST_PLAY_ERROR = -1

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

def play_error_sound():
    # only play error sound every 30 seconds to avoid spamming the sound in case of repeated errors
    global LAST_PLAY_ERROR, ERROR_SOUND_PATH
    now = time.today()
    if now - LAST_PLAY_ERROR > 30:
        subprocess.run(['aplay', ERROR_SOUND_PATH])
        LAST_PLAY_ERROR = now


class SafeSpotifyWrapper:
    def __init__(self, spotipy_client, error_sound: str = ERROR_SOUND_PATH):
        self._client = spotipy_client
        self._error_sound_path = error_sound
        self._first_error_time = -1

    def renew_spotipy_client(self, new_client):
        if self._client != new_client:
            self._client = new_client

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if callable(attr):
            def safe_call(*args, **kwargs):
                try:
                    return attr(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Spotify method '{name}' failed with: {e}")
                    play_error_sound()
                    self._first_error_time = time.time() if self._first_error_time == -1 else self._first_error_time
                    if self._first_error_time > -1 and time.time() - self._first_error_time > 60:
                        logger.error("Spotify API error occurred multiple times. Restarting spotifyd service.")
                        os.system("systemctl -user restart spotifyd")
                        self._first_error_time = -1
                    return None
            return safe_call
        else:
            return attr


class PlayerSpotify:

    current_uri = None

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
        self._sp = None
        self._device_id = None

        self.nvm = nv_manager()
        self.mpd_host = cfg.getn('playerspotify', 'host')
        self.music_player_status = self.nvm.load(cfg.getn('playerspotify', 'status_file'))
        self.second_swipe_action_dict = {'toggle': self.toggle,
                                         'play': self.play,
                                         'skip': self.next,
                                         'rewind': self.rewind,
                                         'replay': self.replay,
                                         'replay_if_stopped': self.replay_if_stopped}
        self.second_swipe_action = None
        self.decode_2nd_swipe_option()

        self.end_of_playlist_next_action = utils.get_config_action(cfg,
                                                                   'playerspotify',
                                                                   'end_of_playlist_next_action',
                                                                   'none',
                                                                   {'rewind': self.rewind,
                                                                    'stop': self.stop,
                                                                    'none': lambda: None},
                                                                   logger)
        self.stopped_prev_action = utils.get_config_action(cfg,
                                                           'playerspotify',
                                                           'stopped_prev_action',
                                                           'prev',
                                                           {'rewind': self.rewind,
                                                            'prev': self.prev,
                                                            'none': lambda: None},
                                                           logger)
        self.stopped_next_action = utils.get_config_action(cfg,
                                                          'playerspotify',
                                                          'stopped_next_action',
                                                          'next',
                                                          {'rewind': self.rewind,
                                                           'next': self.next,
                                                           'none': lambda: None},
                                                          logger)
        self.current_uri = None

    @property
    def device_id(self):
        if self._device_id:
            return self._device_id
        device_id = self.get_device_id()
        if not device_id:
            logger.error("No Spotify device found. Please check your Spotify setup.")
            play_error_sound()
            return None
        self._device_id = device_id
        return self._device_id

    @property
    def sp(self):
        if self._sp:
            self._sp.renew_spotipy_client(self.refresh_access_token())
        else:
            self._sp = SafeSpotifyWrapper(self.authenticate())
        return self._sp

    def exit(self):
        self.sp.pause_playback(device_id=self.device_id)
        self.music_player_status.save_to_json()

    def authenticate(self):
        token_info = self.sp_oauth.get_cached_token()
        if not token_info:
            logger.error("Please authenticate Spotify manually and restart the client.")
            return None
        return spotipy.Spotify(auth=token_info['access_token'])

    def authenticate_manual(self):
        print("\nPlease authenticate Spotify manually:")
        auth_url = self.sp_oauth.get_authorize_url()
        print(f"Open the following URL and paste the redirect URL after login:\n{auth_url}")
        response = input("Paste redirect URL here: ").strip()
        code = self.sp_oauth.parse_response_code(response)
        token_info = self.sp_oauth.get_access_token(code)
        return spotipy.Spotify(auth=token_info['access_token'])

    def refresh_access_token(self):
        token_info = self.sp_oauth.get_cached_token()
        if token_info and self.sp_oauth.is_token_expired(token_info):
            logger.info("Refreshing Spotify access token...")
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
        return spotipy.Spotify(auth=token_info['access_token'])

    def get_device_id(self):
        devices = self.sp.devices().get('devices', [])
        for d in devices:
            if d['name'] == DEVICE_NAME:
                return d['id']
        logger.warning(f"Device '{DEVICE_NAME}' not found.")
        return None

    def decode_2nd_swipe_option(self):
        cfg_2nd_swipe_action = cfg.setndefault('playerspotify', 'second_swipe_action', 'alias', value='none').lower()
        if cfg_2nd_swipe_action not in [*self.second_swipe_action_dict.keys(), 'none', 'custom']:
            logger.error(f"Config spotify.second_swipe_action must be one of "
                         f"{[*self.second_swipe_action_dict.keys(), 'none', 'custom']}. Ignore setting.")
        if cfg_2nd_swipe_action in self.second_swipe_action_dict.keys():
            self.second_swipe_action = self.second_swipe_action_dict[cfg_2nd_swipe_action]
        if cfg_2nd_swipe_action == 'custom':
            custom_action = utils.decode_rpc_call(cfg.getn('playerspotify', 'second_swipe_action', default=None))
            self.second_swipe_action = functools.partial(plugs.call_ignore_errors,
                                                         custom_action['package'],
                                                         custom_action['plugin'],
                                                         custom_action['method'],
                                                         custom_action['args'],
                                                         custom_action['kwargs'])

    def play_uri(self, uri):
        self.current_uri = uri
        if not self.device_id:
            return
        if uri.startswith('spotify:playlist:'):
            self.sp.start_playback(device_id=self.device_id, context_uri=uri)
        elif uri.startswith('spotify:track:'):
            self.sp.start_playback(device_id=self.device_id, uris=[uri])
        else:
            logger.error(f"Unsupported URI: {uri}")

    def playback_control(self, command):
        if not self.device_id:
            return
        try:
            if command == "play":
                self.sp.start_playback(device_id=self.device_id)
            elif command in ("pause", "stop"):
                self.sp.pause_playback(device_id=self.device_id)
            elif command == "next":
                # do nothing if it is a single track, else skip to next track
                if ":track:" not in self.current_uri:
                    self.sp.next_track(device_id=self.device_id)
            elif command == "previous":
                # start from beginning of track if it is a single track, else skip to previous track
                if ":track:" in self.current_uri:
                    self.seek(0)
                else:
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
        playback = self.sp.current_playback()
        if playback:
            vol = playback['device']['volume_percent']
            new_vol = max(0, min(100, vol + change))
            self.sp.volume(new_vol, device_id=self.device_id)

    def current_track(self):
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
        playlists = self.sp.current_user_playlists()
        return [(p['name'], p['uri']) for p in playlists['items']]

    def reset_current_playback(self):
        """
        Reset the current playback state, i.e. clear the current song and reset the elapsed time.
        This is used when a new folder is played or the playback is stopped.
        """
        self.current_uri = None
        self.sp.pause_playback(device_id=self.device_id)
        # self.nvm.save(cfg.getn('playerspotify', 'status_file'), self.music_player_status)

    # interface for jukebox.plugs
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
        self.playback_control("play")

    @plugs.tag
    def stop(self):
        self.playback_control("stop")

    @plugs.tag
    def pause(self, state: int = 1):
        if state == 1:
            self.playback_control("pause")
        else:
            self.play()

    @plugs.tag
    def prev(self):
        self.playback_control("previous")

    @plugs.tag
    def next(self):
        self.playback_control("next")

    @plugs.tag
    def seek(self, seconds: int):
        logger.debug(f"Seek track to {seconds} seconds.")
        self.sp.seek_track(position_ms=seconds, device_id=self.device_id)
        time.sleep(0.5)  # allow API to update position
        self.play()  # resume if needed

    @plugs.tag
    def rewind(self):
        """Re-start current playlist from first track."""
        raise NotImplementedError

    @plugs.tag
    def replay(self):
        """Re-start playing the last-played folder."""
        raise NotImplementedError

    @plugs.tag
    def toggle(self):
        self.playback_control("toggle")

    @plugs.tag
    def replay_if_stopped(self):
        self.play()

    @plugs.tag
    def shuffle(self, option='toggle'):
        current = self.sp.current_playback()
        if current:
            state = current.get('shuffle_state', False)
            self.sp.shuffle(not state, device_id=self.device_id)

    @plugs.tag
    def repeat(self, option='toggle'):
        current = self.sp.current_playback()
        if current:
            mode = current.get('repeat_state', 'off')
            next_mode = {'off': 'context', 'context': 'track', 'track': 'off'}[mode]
            self.sp.repeat(next_mode, device_id=self.device_id)

    @plugs.tag
    def get_current_song(self, param):
        return self.current_track()

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
        if not self.device_id:
            return
        is_second_swipe = self.current_uri == song_url

        if is_second_swipe and self.second_swipe_action:
            logger.debug("Second swipe detected, resuming playback.")
            self.second_swipe_action()
            return
        self.play_uri(song_url)

    @plugs.tag
    def resume(self):
        self.play()

    @plugs.tag
    def fast_forward(self, seconds: float = 1):
        """ Fast forward the current song by a given number of seconds. Rewind if seconds is negative."""
        logger.debug(f"Fast forwarding {seconds} seconds.")
        playback = self.sp.current_playback()
        if playback and playback["item"] and playback["progress_ms"]:
            current_position = playback["progress_ms"]
            track_duration = playback["item"]["duration_ms"]
            jump_to = max(0, min(current_position + seconds * 1000, track_duration - 1000))
            self.seek(int(jump_to))
        else:
            self.logger.error("Cannot fast-forward: No track currently playing.")

    @plugs.tag
    def play_hold_jingle(self, jingle_path: str):
        """
        Play a jingle while the card is held on the reader.
        This is used to indicate that the system is waiting for a second swipe or action.
        """
        logger.debug('Playing jingle:', jingle_path)
        self.stop()
        subprocess.run(['aplay', jingle_path])

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

    def _update_player_status(self):
        playback = self.sp.current_playback()
        if not playback or not playback.get('item'):
            self.music_player_status['artist'] = None
            self.music_player_status['status'] = 'paused'
            self.music_player_status['track'] = None
            self.music_player_status['device'] = None
            self.music_player_status['volume'] = None
            self.music_player_status['progress'] = 0
            self.music_player_status['duration'] = 0
            self.music_player_status['shuffle'] = None
            self.music_player_status['repeat'] = None
        else:
            item = playback['item']
            self.music_player_status['artist'] = ", ".join([a['name'] for a in item['artists']])
            self.music_player_status['status'] = 'playing' if playback['is_playing'] else 'paused'
            self.music_player_status['track'] = item['name']
            self.music_player_status['device'] = playback['device']['name']
            self.music_player_status['volume'] = playback['device']['volume_percent']
            self.music_player_status['progress'] = playback['progress_ms'] // 1000
            self.music_player_status['duration'] = item['duration_ms'] // 1000
            self.music_player_status['shuffle'] = playback['shuffle_state']
            self.music_player_status['repeat'] = playback['repeat_state']

    @plugs.tag
    def playerstatus(self):
        self._update_player_status()
        return self.music_player_status

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


# ---------------------------------------------------------------------------
# Plugin Initializer / Finalizer
# ---------------------------------------------------------------------------

player_ctrl: PlayerSpotify
#: Callback handler instance for play_card events.
#: - is executed when play_card function is called
#: States:
#: - See :class:`PlayCardState`
#: See :class:`PlayContentCallbacks`
play_card_callbacks: PlayContentCallbacks[PlayCardState]


selected = cfg.getn('modules', 'named', 'player')
if selected == 'playerspotify':
    @plugs.initialize
    def initialize():
        """Create and register Spotify player if selected.

        The module ``playerspotify`` may also be imported indirectly by the hybrid
        player; we only register the plugin when ``modules.named.player`` equals
        ``playerspotify``.  Otherwise the initializer returns silently.
        """
        global player_ctrl
        player_ctrl = PlayerSpotify()
        plugs.register(player_ctrl, name='ctrl')

        global play_card_callbacks
        play_card_callbacks = PlayContentCallbacks[PlayCardState]('play_card_callbacks', logger, context=None)


    @plugs.atexit

    def atexit(**ignored_kwargs):
        global player_ctrl
        return player_ctrl.exit()

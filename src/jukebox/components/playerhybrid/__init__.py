# -*- coding: utf-8 -*-
"""
Package for interfacing with the Hybrid Music Player Daemon
"""

import logging
import components.player
import jukebox.cfghandler
import jukebox.plugs as plugs
import simpleaudio
import misc


from .playcontentcallback import PlayContentCallbacks, PlayCardState

from components.playermpd import PlayerMPD
from components.playerspotify import PlayerSpotify

logger = logging.getLogger('jb.PlayerMPD')
cfg = jukebox.cfghandler.get_handler('jukebox')


class PlayerHybrid:
    """Interface to Hyprid Music Player Daemon"""

    def __init__(self):
        self._player_mpd = PlayerMPD()
        self._player_spotify = PlayerSpotify()
        # set mpd as default player
        self.current_player = self._player_mpd

    def exit(self):
        logger.debug("Exit routine of players started")
        self._player_spotify.exit()
        return self._player_mpd.exit()

    def connect(self):
        self.player_mpd.connect()

    def decode_repeat_mode(self):
        self.current_player.decode_repeat_mode()

    def decode_2nd_swipe_option(self):
        self.current_player.decode_2nd_swipe_option()

    def set_current_player(self, player):
        """
        Set the current player based on the player type.
        :param player: PlayerMPD or PlayerSpotify
        """
        if self.current_player != player:
            logger.debug("Switching player")
            self.current_player.reset_current_playback()
            self.current_player = player

    @plugs.tag
    def get_player_type_and_version(self):
        return self.current_player.get_player_type_and_version()

    @plugs.tag
    def update(self):
        return self.current_player.update()

    @plugs.tag
    def update_wait(self):
        return self.current_player.update_wait()

    @plugs.tag
    def play(self):
        self.current_player.play()

    @plugs.tag
    def stop(self):
        self.current_player.stop()

    @plugs.tag
    def pause(self, state: int = 1):
        self.current_player.pause(state)

    @plugs.tag
    def prev(self):
        self.current_player.prev()

    @plugs.tag
    def next(self):
        self.current_player.next()

    @plugs.tag
    def seek(self, new_time):
        self.current_player.seek(new_time)

    @plugs.tag
    def rewind(self):
        self.current_player.rewind()

    @plugs.tag
    def replay(self):
        self.current_player.replay()

    @plugs.tag
    def toggle(self):
        self.current_player.toggle()

    @plugs.tag
    def replay_if_stopped(self):
        self.current_player.replay_if_stopped()

    @plugs.tag
    def shuffle(self, option='toggle'):
        self.current_player.shuffle(option)

    @plugs.tag
    def repeat(self, option='toggle'):
        self.current_player.repeat(option)

    @plugs.tag
    def get_current_song(self, param):
        return self.current_player.get_current_song(param)

    @plugs.tag
    def map_filename_to_playlist_pos(self, filename):
        self.current_player.map_filename_to_playlist_pos(filename)

    @plugs.tag
    def remove(self):
        self.current_player.remove()

    @plugs.tag
    def move(self):
        self.current_player.move()

    @plugs.tag
    def play_single(self, song_url):
        logger.debug(f"Playing single song: {song_url}")
        if song_url.startswith('spotify:'):
            self.set_current_player(self._player_spotify)
            self._player_mpd.stop()
        else:
            self.set_current_player(self._player_mpd)
            self._player_spotify.stop()
        self.current_player.play_single(song_url)
        

    @plugs.tag
    def resume(self):
        self.current_player.resume()

    @plugs.tag
    def fast_forward(self, seconds: float = 1):
        self.current_player.fast_forward(seconds)

    @plugs.tag
    def play_hold_jingle(self, jingle_path: str):
        """
        Play a jingle while the card is held on the reader.
        This is used to indicate that the system is waiting for a second swipe or action.
        """
        # logger.debug('Playing jingle:', jingle_path)
        self.current_player.pause()
        wave_obj = simpleaudio.WaveObject.from_wave_file(jingle_path)
        wave_obj.play()

    @plugs.tag
    def play_card(self, folder: str, recursive: bool = False):
        logger.debug(f"Playing folder: {folder}")
        if folder.startswith('spotify:'):
            self.set_current_player(self._player_spotify)
        else:
            self.set_current_player(self._player_mpd)
        self.current_player.play_card(folder, recursive)

    @plugs.tag
    def get_single_coverart(self, song_url):
        return self.current_player.get_single_coverart(song_url)

    @plugs.tag
    def get_album_coverart(self, albumartist: str, album: str):
        return self.current_player.get_album_coverart(albumartist, album)

    @plugs.tag
    def flush_coverart_cache(self):
        return self.current_player.flush_coverart_cache()

    @plugs.tag
    def get_folder_content(self, folder: str):
        return self.current_player.get_folder_content(folder)

    @plugs.tag
    def play_folder(self, folder: str, recursive: bool = False) -> None:
        logger.debug(f"Playing folder: {folder}")
        if folder.startswith('spotify:'):
            self.set_current_player(self._player_spotify)
        else:
            self.set_current_player(self._player_mpd)
        self.current_player.play_folder(folder, recursive)

    @plugs.tag
    def play_album(self, albumartist: str, album: str):
        logger.debug(f"Playing album: {album}")
        if album.startswith('spotify:'):
            self.set_current_player(self._player_spotify)
        else:
            self.set_current_player(self._player_mpd)
        self.current_player.play_album(albumartist, album)

    @plugs.tag
    def queue_load(self, folder):
        self.current_player.queue_load(folder)

    @plugs.tag
    def playerstatus(self):
        return self.current_player.playerstatus()

    @plugs.tag
    def playlistinfo(self):
        return self.current_player.playlistinfo()

    @plugs.tag
    def list_all_dirs(self):
        return self.current_player.list_all_dirs()

    @plugs.tag
    def list_albums(self):
        return self.current_player.list_albums()

    @plugs.tag
    def list_songs_by_artist_and_album(self, albumartist, album):
        return self.current_player.list_songs_by_artist_and_album(albumartist, album)

    @plugs.tag
    def get_song_by_url(self, song_url):
        return self.current_player.get_song_by_url(song_url)

# ---------------------------------------------------------------------------
# Plugin Initializer / Finalizer
# ---------------------------------------------------------------------------

player_ctrl: PlayerHybrid
#: Callback handler instance for play_card events.
#: - is executed when play_card function is called
#: States:
#: - See :class:`PlayCardState`
#: See :class:`PlayContentCallbacks`
play_card_callbacks: PlayContentCallbacks[PlayCardState]


@plugs.initialize
def initialize():
    global player_ctrl
    player_ctrl = PlayerHybrid()
    plugs.register(player_ctrl, name='ctrl')

    global play_card_callbacks
    play_card_callbacks = PlayContentCallbacks[PlayCardState]('play_card_callbacks', logger, context=None)

    # Update mpc library
    library_update = cfg.setndefault('playerhybrid', 'library', 'update_on_startup', value=True)
    if library_update:
        player_ctrl.update()

    # Check user rights on music library
    library_check_user_rights = cfg.setndefault('playerhybrid', 'library', 'check_user_rights', value=True)
    if library_check_user_rights is True:
        music_library_path = components.player.get_music_library_path()
        if music_library_path is not None:
            logger.info(f"Change user rights for {music_library_path}")
            misc.recursive_chmod(music_library_path, mode_files=0o666, mode_dirs=0o777)


@plugs.atexit
def atexit(**ignored_kwargs):
    global player_ctrl
    return player_ctrl.exit()

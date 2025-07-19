# -*- coding: utf-8 -*-
"""
Package for interfacing with the Hybrid Music Player Daemon
"""

import os
import mpd
import threading
import logging
import time
import functools
from pathlib import Path
import components.player
import jukebox.cfghandler
import jukebox.utils as utils
import jukebox.plugs as plugs
import jukebox.multitimer as multitimer
import jukebox.publishing as publishing
import jukebox.playlistgenerator as playlistgenerator
import misc
import simpleaudio

from jukebox.NvManager import nv_manager
from .playcontentcallback import PlayContentCallbacks, PlayCardState
from .coverart_cache_manager import CoverartCacheManager

from components.playermpd import PlayerMPD
# from jukebox.components.playerspotify import SpotifyController

logger = logging.getLogger('jb.PlayerMPD')
cfg = jukebox.cfghandler.get_handler('jukebox')

class PlayerHybrid:
    """Interface to Hyprid Music Player Daemon"""

    
    player_mpd = PlayerMPD()
    # player_spotify = SpotifyController()

    def __init__(self):
        self.player_mpd.__init__()
        # self.player_spotify.init()

    def exit(self):
        logger.debug("Exit routine of players started")
        return self.player_mpd.exit()

    def connect(self):
        self.player_mpd.connect()

    def decode_repeat_mode(self):
        """
        Decodes the replay action from the configuration file and sets it accordingly.
        """
        self.player_mpd.decode_repeat_mode()
        self.player_spotify.decode_repeat_mode()

    def decode_2nd_swipe_option(self):
        self.player_mpd.decode_2nd_swipe_option()
        self.player_spotify.decode_2nd_swipe_option()

    @plugs.tag
    def get_player_type_and_version(self):
        return self.player_mpd.get_player_type_and_version()

    @plugs.tag
    def update(self):
        return self.player_mpd.update()

    @plugs.tag
    def update_wait(self):
        return self.player_mpd.update_wait()

    @plugs.tag
    def play(self):
        self.player_mpd.play()

    @plugs.tag
    def stop(self):
        self.player_mpd.stop()

    @plugs.tag
    def pause(self, state: int = 1):
        self.player_mpd.pause(state)

    @plugs.tag
    def prev(self):
        self.player_mpd.prev()

    @plugs.tag
    def next(self):
        self.player_mpd.next()

    @plugs.tag
    def seek(self, new_time):
        self.player_mpd.seek(new_time)

    @plugs.tag
    def rewind(self):
        self.player_mpd.rewind()

    @plugs.tag
    def replay(self):
        self.player_mpd.replay()

    @plugs.tag
    def toggle(self):
        self.player_mpd.toggle()

    @plugs.tag
    def replay_if_stopped(self):
        self.player_mpd.replay_if_stopped()

    @plugs.tag
    def shuffle(self, option='toggle'):
        self.player_mpd.shuffle(option)

    @plugs.tag
    def repeat(self, option='toggle'):
        self.player_mpd.repeat(option)

    @plugs.tag
    def get_current_song(self, param):
        return self.player_mpd.get_current_song(param)

    @plugs.tag
    def map_filename_to_playlist_pos(self, filename):
        self.player_mpd.map_filename_to_playlist_pos(filename)

    @plugs.tag
    def remove(self):
        self.player_mpd.remove()

    @plugs.tag
    def move(self):
        self.player_mpd.move()

    @plugs.tag
    def play_single(self, song_url):
        self.player_mpd.play_single(song_url)

    @plugs.tag
    def resume(self):
        self.player_mpd.resume()

    @plugs.tag
    def fast_forward(self, seconds: float = 1):
        self.player_mpd.fast_forward(seconds)

    @plugs.tag
    def play_hold_jingle(self, jingle_path: str):
        self.player_mpd.play_hold_jingle(jingle_path)
        # """
        # Play a jingle while the card is held on the reader.
        # This is used to indicate that the system is waiting for a second swipe or action.
        # """
        # logger.debug('Playing jingle:', jingle_path)
        # with self.mpd_lock:
        #     self.mpd_client.stop()
        #     wave_obj = simpleaudio.WaveObject.from_wave_file(jingle_path)
        #     wave_obj.play()

    @plugs.tag
    def play_card(self, folder: str, recursive: bool = False):
        self.player_mpd.play_card(folder, recursive)

    @plugs.tag
    def get_single_coverart(self, song_url):
        return self.player_mpd.get_single_coverart(song_url)

    @plugs.tag
    def get_album_coverart(self, albumartist: str, album: str):
        return self.player_mpd.get_album_coverart(albumartist, album)

    @plugs.tag
    def flush_coverart_cache(self):
        return self.player_mpd.flush_coverart_cache()

    @plugs.tag
    def get_folder_content(self, folder: str):
        return self.player_mpd.get_folder_content(folder)

    @plugs.tag
    def play_folder(self, folder: str, recursive: bool = False) -> None:
        self.player_mpd.play_folder(folder, recursive)

    @plugs.tag
    def play_album(self, albumartist: str, album: str):
        self.player_mpd.play_album(albumartist, album)

    @plugs.tag
    def queue_load(self, folder):
        self.player_mpd.queue_load(folder)

    @plugs.tag
    def playerstatus(self):
        return self.player_mpd.playerstatus()

    @plugs.tag
    def playlistinfo(self):
        return self.player_mpd.playlistinfo()

    @plugs.tag
    def list_all_dirs(self):
        return self.player_mpd.list_all_dirs()

    @plugs.tag
    def list_albums(self):
        return self.player_mpd.list_albums()

    @plugs.tag
    def list_songs_by_artist_and_album(self, albumartist, album):
        return self.player_mpd.list_songs_by_artist_and_album(albumartist, album)

    @plugs.tag
    def get_song_by_url(self, song_url):
        return self.player_mpd.get_song_by_url(song_url)

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
    play_card_callbacks = PlayContentCallbacks[PlayCardState]('play_card_callbacks', logger, context=player_ctrl.player_mpd.mpd_lock)

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

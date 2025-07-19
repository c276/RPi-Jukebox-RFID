from .playerspotify import SpotifyController

spotify = SpotifyController()

def play(uri=None):
    if uri:
        spotify.play_uri(uri)
    else:
        spotify.play()

def pause():
    spotify.pause()

def resume():
    spotify.play()

def stop():
    spotify.pause()

def next():
    spotify.next_track()

def previous():
    spotify.previous_track()

def volume_up():
    spotify.volume_up()

def volume_down():
    spotify.volume_down()

def status():
    return spotify.current_status()

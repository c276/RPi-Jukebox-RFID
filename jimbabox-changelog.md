# git diff future3/develop future3/jimbabox

## jukebox
src/jukebox/components/gpio/gpioz/core/input_devices.py
* countinglongpressbutton

src/jukebox/components/gpio/gpioz/plugin/__init__.py
* validity check

src/jukebox/components/playerhybrid/__init__.py
* completely new

src/jukebox/components/playerhybrid/playcontentcallback.py
* completely new

src/jukebox/components/playermpd/__init__.py
* lots of stuff

src/jukebox/components/playerspotify/__init__.py
* new

src/jukebox/components/playerspotify/playerspotify.py
* new

src/jukebox/components/rfid/hardware/rc522_spi/rc522_spi.py
* set logger config to better match format of other modules

src/jukebox/components/rfid/reader/__init__.py
* add same id delay
* add logic to ignore false-positive no-card detections for x iterations
* do not send card action if card_id == previous_id

src/jukebox/components/rpc_command_alias.py
* add play_spotify, fast_forward, play_hold_jingle commands

src/jukebox/components/synchronisation/rfidcards/__init__.py
* change default player from mpd to hybrid

src/jukebox/components/timers/idle_shutdown_timer.py
* some experiments and possible fixes, need to check if these need to stay

tools/battery_monitor.py
* new

tools/spotify_control.py
* new

tools/test-mpu6050.py
* new

## webapp
src/webapp/package-lock.json
src/webapp/public/index.html
src/webapp/public/locales/de/translation.json
src/webapp/public/locales/en/translation.json
src/webapp/src/commands/index.js
src/webapp/src/components/Cards/controls/actions/play-spotify/index.js
src/webapp/src/components/Cards/controls/controls-selector.js
src/webapp/src/config.js

## documentation
installation/README.md
installation/install-jukebox.sh
jimbabox.odt
readme-bedienung.txt
requirements.txt
* probably not complete yet

## resources
resources/audio/error.mp3
resources/audio/error.wav
resources/audio/fast_forward_jingle.wav
resources/audio/rewind_jingle.wav

## custom services
resources/default-services/battery-monitor.service
resources/default-services/jukebox-log-export.service
resources/default-services/jukebox-log-export.timer
resources/default-services/spotifyd.service
resources/default-settings/spotifyd.conf

## custom settings
shared/settings/cards.yaml
shared/settings/gpio.yaml
shared/settings/jukebox.yaml
shared/settings/logger.yaml
shared/settings/rfid.yaml
shared/settings/spotifyd.conf
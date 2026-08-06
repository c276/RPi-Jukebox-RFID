# Jukebox Installation Routines

## Logging - Bash Script output rules

```bash
run_and_print_lc "Run a command and log its output to both console and logfile"
print_lc         "This message will be logged to both console and logfile"
print_c          "This message will only be logged to the console"
log              "This message will only be logged to the logfile"
clear_c          "Clears the console screen"
```

[Learn more about bash script outputs](https://stackoverflow.com/questions/18460186/writing-outputs-to-log-file-and-console)

## Installation

[Install Phoniebox software](../documentation/builders/installation.md#install-phoniebox-software)

[Install Spotify]
For now, just manual installation.

Download binary

```bash
sudo apt install curl unzip -y
curl -LO https://github.com/Spotifyd/spotifyd/releases/latest/download/spotifyd-linux-armv7-slim.tar.gz
tar -xzf spotifyd-linux-armv7-slim.tar.gz
sudo mv spotifyd /usr/local/bin/
```

Configure

```bash
cp ~/RPi-Jukebox-RFID/resources/default-settings/spotifyd.conf ~/RPi-Jukebox-RFID/shared/settings/spotifyd.conf
 echo "spotify-user" > ~/.config/spotifyd/spotify_username # NOTE: leading space to remove command from command history!
 echo "spotify-password" > ~/.config/spotifyd/spotify_password # NOTE: leading space to remove command from command history!
sudo cp ~/RPi-Jukebox-RFID/resources/default-services/spotifyd.service usr/lib/systemd/user/spotifyd.service
sudo nano usr/lib/systemd/user/spotifyd.service # check if the config path is correct!
```

Enable and start user service

```bash
systemctl --user daemon-reexec
systemctl --user daemon-reload
systemctl --user enable spotifyd
systemctl --user start spotifyd
```

Optional: enable linger for current user

```bash
sudo loginctl enable-linger $USER
```

NOTE: may cause shutdown issues as user services are not stopped properly with linger enabled.
Disable with

```bash
sudo loginctl disable-linger $USER
```

Check with

```bash
journalctl -u spotifyd -f
```

or

```bash
systemctl --user status spotifyd
```

[Enable logfile for jukebox]
Copy service and timer files

```bash
sudo cp resources/default-services/jukebox-log-export.service ~/.config/systemd/user/.
sudo cp resources/default-services/jukebox-log-export.timer ~/.config/systemd/user/.
```

Enable deamon & start timer

```bash
systemctl --user daemon-reload
systemctl --user enable --now jukebox-log-export.timer
```

[Battery monitor]
with ina219

```bash
sudo cp /home/pi/RPi-Jukebox-RFID/resources/default-services/battery-monitor.service /etc/systemd/system/battery-monitor.service

sudo systemctl enable battery-monitor.service
sudo systemctl start battery-monitor.service
```

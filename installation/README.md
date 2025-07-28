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
sudo cp ~/RPi-Jukebox-RFID/resources/default-settings/spotifyd.conf ~/RPi-Jukebox-RFID/shared/settings/spotifyd.conf
nano ~/RPi-Jukebox-RFID/shared/settings/spotifyd.conf # add username
 echo "spotify-password" > ~/.config/spotifyd/spotify_password # NOTE: leading space to remove command from command history!
sudo cp ~/RPi-Jukebox-RFID/resources/default-services/spotifyd.service /etc/systemd/system/spotifyd.service
sudo nano /etc/systemd/system/spotifyd.service # check if the config path is correct!
```
Enable and start service (TODO: enable as user service like the jukebox daemon?!)
```bash
sudo systemctl daemon-reexec
sudo systemctl enable spotifyd
sudo systemctl start spotifyd
```
Check with
```bash
journalctl -u spotifyd -f
```


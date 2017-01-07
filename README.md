# sonarrAnnounced

## Requirements
1) Python 3.5.2 or newer

## Installation (on Debian Jessie)
1. Install Python 3.5.2
2. Install pip `sudo easy_install pip`
3. `cd /opt`
4. Clone project `git clone https://github.com/l3uddz/sonarrAnnounced`
- `cd sonarrAnnounced`
5. Install requirements.txt `sudo pip3.5 install -r requirements.txt`
6. Configure settings.cfg.default (leave auth_key/torrent_pass empty to keep a tracker disabled)
7. `mv settings.cfg.default settings.cfg`
8. Edit systemd/announced.service with your user
- `sudo cp announced.service /etc/systemd/system/announced.service`
9. `sudo systemctl daemon-reload`
10. `sudo systemctl start announced`
11. Check your status.log file that should have been created to ensure it is operating correctly and parsing messages `tail -f status.log`
12. Enable start at boot if you wish, `sudo systemctl enable announced`

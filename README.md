# sonarrAnnounced

Python script to notify sonarr of tracker announcements from IRC announce channels. 

## Requirements
1. Python 3.5.2 or newer
2. requirements.txt modules

## Supported Trackers
1. BTN
2. MTV
3. IPTorrents
4. Nebulance
5. HD-Torrents
6. XSpeeds
7. FileList

Open to suggestions/pull requests!

## To-Do


## Feature Requests
Request features at [FeatHub](http://feathub.com/l3uddz/sonarrAnnounced)


# Installation (on Debian Jessie)
## Python 3.5.2

1. `wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tar.xz`
2. `tar xvf Python-3.5.2.tar.xz`
3. `cd Python-3.5.2`
4. `sudo apt-get install make git build-essential libssl-dev zlib1g-dev libbz2-dev libsqlite3-dev`
5. `sudo ./configure --enable-loadable-sqlite-extensions && sudo make && sudo make install`

This should automatically install pip3.5 for you

## sonarrAnnounced
1. `cd /opt`
2. `sudo git clone https://github.com/l3uddz/sonarrAnnounced`
3. `sudo chown -R user:group sonarrAnnounced`
4. `sudo pip3.5 install -r /opt/sonarrAnnounced/requirements.txt`
5. `mv settings.cfg.default settings.cfg`
6. `nano settings.cfg`
- Configure it how you want
7. Edit systemd/announced.service with your user and group
8. `sudo cp announced.service /etc/systemd/system/announced.service`
9. `sudo systemctl daemon-reload`
10. `sudo systemctl start announced`
- Check it is working properly, http://localhost:PORT - use user/pass you chosen in the [server] section of settings.cfg
11. if you want auto start @ boot, `sudo systemctl enable announced`

# Installation videos
1. Debian Jessie: https://youtu.be/oLiGMcUWiB0
2. Windows: https://youtu.be/UbHwFqkLc0c

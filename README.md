# sonarrAnnounced

## Installation (on Debian Jessie)
1. Install Python 3.x PIP `sudo easy_install pip`
2. Set /opt owner `sudo chown -R user:user /opt`
- `cd /opt`
3. Clone project `git clone https://github.com/l3uddz/sonarrAnnounced`
- `cd sonarrAnnounced`
4. Install requirements.txt `sudo pip3 install -r requirements.txt`
5. `python3 bot.py`
6. Edit settings.cfg (leave user/pass of tracker empty to disable and not initialize that tracker)
7. `sudo apt-get install screen`
8. `sudo chmod +x run.sh`
9. `./run.sh`
10. `screen -r` (attaches to screen so you can see live debug messages)
11. Ctrl A+D to detach and keep screen running, repeat previous step to reattach/view.

import datetime
import logging

import config
import db
import sonarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "BTN"
irc_host = "irc.broadcasthe.net"
irc_port = 6667
irc_channel = "#BTN-Announce"
irc_tls = False
irc_tls_verify = False

# these are loaded by init
auth_key = None
torrent_pass = None

logger = logging.getLogger(name.upper())
logger.setLevel(logging.DEBUG)

############################################################
# Tracker Framework (all trackers must follow)
############################################################
# Parse announcement message
torrent_title = None


@db.db_session
def parse(announcement):
    global name, torrent_title
    decolored = utils.strip_irc_color_codes(announcement)

    # extract required information from decolored
    if 'NOW BROADCASTING' in decolored:
        torrent_title = utils.substr(decolored, '[ ', ' ]', True)
    torrent_id = utils.get_id(decolored, 1)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

        announced = db.Announced(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                 indexer=name, torrent=download_link)
        approved = sonarr.wanted(torrent_title, download_link, name)
        if approved:
            logger.debug("Sonarr approved release: %s", torrent_title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                   indexer=name, torrent=download_link)
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)
        torrent_title = None


# Generate torrent link
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://broadcasthe.net/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
        .format(torrent_id, auth_key, torrent_pass)
    return torrent_link


# Initialize tracker
def init():
    global auth_key, torrent_pass

    auth_key = cfg["{}.auth_key".format(name.lower())]
    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]

    # check auth_key && torrent_pass was supplied
    if not auth_key or not torrent_pass:
        return False

    return True

import logging

import config
import db
import sonarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "MoreThan"
irc_host = "irc.morethan.tv"
irc_port = 6667
irc_channel = "#announce"
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
def parse(announcement):
    global name

    # extract required information from announcement
    torrent_title = utils.str_before(announcement, ' - ')
    torrent_id = utils.get_id(announcement, 1)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

        announced, created = db.Announced.get_or_create(title=torrent_title, indexer=name)
        approved = sonarr.wanted(torrent_title, download_link, name)
        if approved:
            logger.debug("Sonarr approved release: %s", torrent_title)
            snatched, created = db.Snatched.get_or_create(title=torrent_title, indexer=name)
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)


# Generate torrent link
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://www.morethan.tv/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
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

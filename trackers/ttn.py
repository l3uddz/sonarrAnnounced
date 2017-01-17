import datetime
import logging
import re

import config
import db
import sonarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "TTN"
irc_host = "irc.transmithe.net"
irc_port = 6667
irc_channel = "#ttn-announce"
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
@db.db_session
def parse(announcement):
    decolored = utils.strip_irc_color_codes(announcement)
    if '[Episode]' not in decolored:
        return

    # extract required information from announcement
    torrent_title = parse_torrent_title(decolored)
    if not torrent_title:
        return
    torrent_id = utils.get_id(decolored, 0)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

        announced = db.Announced(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                 indexer=name)
        approved = sonarr.wanted(torrent_title, download_link, name)
        if approved:
            logger.debug("Sonarr approved release: %s", torrent_title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                   indexer=name)
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)


# Generate torrent link
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://transmithe.net/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
        .format(torrent_id, auth_key, torrent_pass)
    return torrent_link


# Initialize tracker
def init():
    global auth_key, torrent_pass

    auth_key = cfg["{}.auth_key".format(name.lower())]
    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]

    # check torrent_pass was supplied
    if not auth_key or not torrent_pass:
        return False

    return True


# Parse torrent title from message (accounting for TTN video detail parts (WebDL / MKV / 720p / etc....))
def parse_torrent_title(message):
    rxp = '\[.*?\] (.*?) \[(.*?)\]\s'
    m = re.search(rxp, message)
    if m and len(m.groups()) >= 2:
        if '/' not in m.group(2):
            logger.debug("Was expecting ' / ' seperated video details - found: '%s'", m.group(2))
            return None

        video_details = m.group(2).split(' / ')
        if len(video_details) < 5:
            logger.debug("Was expecting atleast 5 video detail parts, found: %d parts (%s)", len(video_details),
                         video_details)
            return None

        orig_title = m.group(1).replace(" - ", " ").replace("?", "")
        if orig_title.startswith("@"):
            orig_title = orig_title.replace("@", "At.")
            orig_title = orig_title.replace("-", ".")

        torrent_title = "{0} {1} {2} {3}".format(orig_title, video_details[3], video_details[0].upper(),
                                                 video_details[1])
        if len(video_details) > 5:
            # there was a group attached to this release - add it
            torrent_title += "-{}".format(video_details[5])

        return torrent_title

    return None

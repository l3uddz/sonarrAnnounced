import asyncio
import logging

import config
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################

name = "Develop"
irc_host = "irc.freenode.net"
irc_port = 6667
irc_channel = "#sonarrAnnounced"
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
@asyncio.coroutine
def parse(announcement):
    decolored = utils.strip_irc_color_codes(announcement)
    logger.debug("Parsing: %s", decolored)


# Generate torrent link
@asyncio.coroutine
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://www.google.com"
    return torrent_link


# Initialize tracker
@asyncio.coroutine
def init():
    return True

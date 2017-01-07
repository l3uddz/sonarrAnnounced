import asyncio
import logging
from pathlib import Path

from aiohttp import web, ClientSession, FileSender

import config
import sonarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration (Hands off tracker_* variables)
############################################################
name = "BTN"
irc_host = "irc.broadcasthe.net"
irc_port = 6667
irc_channel = "#BTN-Announce"
irc_tls = False
irc_tls_verify = False

tracker_user = None
tracker_pass = None

logger = logging.getLogger(name.upper())
logger.setLevel(logging.DEBUG)

############################################################
# Tracker Framework (all trackers must follow)
############################################################
# Parse announcement message
torrent_title = None


@asyncio.coroutine
def parse(announcement):
    global name, torrent_title
    decolored = utils.strip_irc_color_codes(announcement)
    logger.debug("Parsing: %s", decolored)

    # extract required information from decolored
    if 'NOW BROADCASTING' in decolored:
        torrent_title = utils.substr(decolored, '[ ', ' ]', True)
    torrent_id = utils.get_id(decolored, 1)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = "http://{}:{}/{}/{}/{}".format(cfg['server.host'], cfg['server.port'],
                                                       name.lower(), torrent_id, torrent_title.replace(' ', '.'))
        approved = yield from sonarr.wanted(torrent_title, download_link, name)
        if approved:
            logger.debug("Sonarr approved release: %s", torrent_title)
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)
        torrent_title = None


# Generate torrent link
@asyncio.coroutine
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://broadcasthe.net/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
        .format(torrent_id, tracker_user, tracker_pass)
    return torrent_link


# Initialize tracker
@asyncio.coroutine
def init():
    global tracker_user, tracker_pass

    tracker_user = cfg["{}.auth_key".format(name.lower())]
    tracker_pass = cfg["{}.torrent_pass".format(name.lower())]

    # check auth_key && torrent_pass was supplied
    if not tracker_user or not tracker_pass:
        return False

    return True


# Route point for grabbing torrents from this tracker
@asyncio.coroutine
def route(request):
    torrent_id = request.match_info.get('id', None)
    torrent_name = request.match_info.get('name', None)
    if not torrent_id or not torrent_name:
        return web.HTTPNotFound()
    logger.debug("Sonarr requested torrent_id: %s - torrent_name: %s", torrent_id, torrent_name)

    # retrieve .torrent link for specified torrent_id (id)
    torrent_link = yield from get_torrent_link(torrent_id, torrent_name)
    if torrent_link is None:
        logger.error("Problem retrieving torrent link for: %s", torrent_id)
        return web.HTTPNotFound()

    # download .torrent
    downloaded, torrent_path = yield from download_torrent(torrent_id, torrent_link)
    if downloaded is False or torrent_path is None:
        logger.error("Problem downloading torrent for: %s @ %s", torrent_id, torrent_link)
        return web.HTTPNotFound()
    elif not utils.validate_torrent(Path(torrent_path)):
        logger.error("Downloaded torrent was invalid, from: %s", torrent_link)
        return web.HTTPNotFound()

    # send torrent as response
    logger.debug("Serving %s to Sonarr", torrent_path)
    sender = FileSender(resp_factory=web.StreamResponse, chunk_size=256 * 1024)
    ret = yield from sender.send(request, Path(torrent_path))
    return ret


# Download the found .torrent file
@asyncio.coroutine
def download_torrent(torrent_id, torrent_link):
    chunk_size = 256 * 1024
    downloaded = False

    # generate filename
    torrents_dir = Path('torrents', name)
    if not torrents_dir.exists():
        torrents_dir.mkdir(parents=True)

    torrent_file = "{}.torrent".format(torrent_id)
    torrent_path = torrents_dir / torrent_file

    # download torrent
    try:
        with ClientSession() as session:
            req = yield from session.get(url=torrent_link)
            if req.status == 200:
                with torrent_path.open('wb') as fd:  # open(torrent_path, 'wb') as fd:
                    while True:
                        chunk = yield from req.content.read(chunk_size)
                        if not chunk:
                            break
                        fd.write(chunk)
            else:
                logger.error("Unexpected response when downloading torrent: %s", torrent_link)
                return False, None

    except Exception as ex:
        logger.exception("Exception downloading torrent: %s to %s", torrent_link, torrent_file)
        return False, None

    finally:
        downloaded = True

    logger.debug("Downloaded: %s", torrent_file)
    return downloaded, torrent_path

import asyncio
import logging
import pickle
from pathlib import Path

from aiohttp import web, ClientSession, FileSender

import config
import sonarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration (Hands off tracker_* variables)
############################################################
name = "IPTorrents"
irc_host = "irc.iptorrents.com"
irc_port = 6667
irc_channel = "#ipt.announce"
irc_tls = False
irc_tls_verify = False

tracker_cookies = {}
tracker_user = None
tracker_pass = None

logger = logging.getLogger(name.upper())
logger.setLevel(logging.DEBUG)


############################################################
# Tracker Framework (all trackers must follow)
############################################################
# Parse announcement message
@asyncio.coroutine
def parse(announcement):
    if 'TV/' not in announcement:
        return

    logger.debug("Parsing: %s", announcement)
    # extract required information from announcement
    torrent_title = utils.substr(announcement, '10 ', ' -', True).rstrip('')
    torrent_id = utils.get_id(announcement)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = "http://{}:{}/{}/{}".format(cfg['server.host'], cfg['server.port'], name.lower(), torrent_id)
        approved = yield from sonarr.wanted(torrent_title, download_link)
        if approved:
            logger.debug("Sonarr approved release: %s", torrent_title)
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)


# Initialize tracker
@asyncio.coroutine
def init():
    global tracker_cookies, tracker_user, tracker_pass
    loaded = False
    landing_url = "https://iptorrents.com/login.php"
    login_url = "https://iptorrents.com/take_login.php"

    # check user/pass specified before continuing
    tracker_user = cfg["{}.user".format(name.lower())]
    tracker_pass = cfg["{}.pass".format(name.lower())]
    if not tracker_user or not tracker_user:
        return loaded

    # check stored cookies before proceeding
    cookie_dir = Path('cookies')
    cookie_file = cookie_dir / "{}.cookies".format(name.lower())
    if not cookie_dir.exists():
        cookie_dir.mkdir(parents=True)
    else:
        if cookie_file.exists():
            tracker_cookies = pickle.load(cookie_file.open('rb'))
            if tracker_cookies is not None and len(tracker_cookies) > 0:
                valid = yield from check_cookies()
                if valid:
                    logger.debug("Using stored cookies as they are still valid")
                    return True

    # retrieve user cookies
    with ClientSession() as session:
        # fetch initial cookies from login page
        req = yield from session.get(url=landing_url)
        yield from req.text()

        # login
        req = yield from session.post(url=login_url, data={'username': tracker_user, 'password': tracker_pass})
        data = yield from req.text()

        # store cookies if login successful
        if 'alt=\"Log Out\"' in data:
            if tracker_cookies is not None and len(tracker_cookies) > 0:
                tracker_cookies.clear()

            logger.debug("Fetched user cookies")
            for cookie in session.cookie_jar:
                if cookie.value is not None:
                    logger.debug("Storing cookie %s: %s", cookie.key, cookie.value)
                    tracker_cookies[cookie.key] = cookie.value

            pickle.dump(tracker_cookies, cookie_file.open('wb'))
            loaded = True
        else:
            logger.error("Failed fetching user cookies")
            logger.debug("Unexpected logged in response:\n%s", data)

    return loaded


# Route point for grabbing torrents from this tracker
@asyncio.coroutine
def route(request):
    torrent_id = request.match_info.get('id', None)
    if not torrent_id:
        return web.HTTPNotFound()
    logger.debug("Sonarr requested torrent_id: %s", torrent_id)

    # retrieve .torrent link for specified torrent_id (id)
    torrent_link = yield from find_torrent(torrent_id)
    if torrent_link is None:
        logger.error("Problem retrieving torrent link for: %s", torrent_id)
        return web.HTTPNotFound()

    # download .torrent
    downloaded, torrent_path = yield from download_torrent(torrent_id, torrent_link)
    if downloaded is False or torrent_path is None:
        logger.error("Problem downloading torrent for: %s @ %s", torrent_id, torrent_link)
        return web.HTTPNotFound()
    elif not utils.validate_torrent(Path(torrent_path)):
        logger.error("Downloaded torrent was invalid, no announcer present for torrent from: %s", torrent_link)
        return web.HTTPNotFound()

    # send torrent as response
    logger.debug("Serving %s to Sonarr", torrent_path)
    sender = FileSender(resp_factory=web.StreamResponse, chunk_size=256 * 1024)
    ret = yield from sender.send(request, Path(torrent_path))
    return ret


# Find the .torrent for the specified torrent_id
@asyncio.coroutine
def find_torrent(torrent_id):
    torrent_link = None

    if tracker_cookies is None or len(tracker_cookies) <= 0:
        logger.error("There were no user cookies stored, ignoring....")
        return torrent_link

    # retrieve .torrent file within torrent details page
    details_url = "http://www.iptorrents.com/details.php?id={}".format(torrent_id)
    with ClientSession(cookies=tracker_cookies) as session:
        req = yield from session.get(url=details_url)
        data = yield from req.text()

        tmp = utils.substr(data, "download.php", ".torrent", False)
        if tmp.endswith(".torrent"):
            torrent_link = "http://www.iptorrents.com/{}".format(tmp)
            logger.debug("Found .torrent: %s", torrent_link)
        else:
            logger.error("Problem locating .torrent: %s", details_url)
            return torrent_link

    return torrent_link


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
        with ClientSession(cookies=tracker_cookies) as session:
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


# Check if stored cookies are valid
@asyncio.coroutine
def check_cookies():
    valid = False
    if tracker_cookies is None or len(tracker_cookies) <= 0:
        return valid

    with ClientSession(cookies=tracker_cookies) as session:
        req = yield from session.get(url='https://iptorrents.com/t')
        data = yield from req.text()
        if 'alt=\"Log Out\"' in data:
            valid = True
        else:
            logger.debug("Stored cookies have expired, renewing...")

    return valid

import asyncio
import logging
from pathlib import Path

import pydle
from aiohttp import web, ClientSession, FileSender
from deco import *

import config
import utils
from trackers import Trackers

############################################################
# Configuration
############################################################

cfg = config.init()

############################################################
# Initialization
############################################################
# Setup logging
logFormatter = logging.Formatter('%(asctime)s - %(name)-20s - %(message)s')
rootLogger = logging.getLogger()

if cfg['bot.debug_file']:
    fileHandler = logging.FileHandler('status.log')
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

if cfg['bot.debug_console']:
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

logger = rootLogger.getChild("BOT")
logger.setLevel(logging.DEBUG)

# Event loop
loop = asyncio.get_event_loop()

# Trackers
trackers = Trackers(loop)
if len(trackers.loaded) <= 0:
    logger.info("No trackers were initialized, exiting...")
    quit()


############################################################
# Torrent Server Routing Points for Loaded Trackers
############################################################
# Sonarr request endpoint
@asyncio.coroutine
def route(request):
    tracker = trackers.get_tracker(request.match_info.get('tracker', None))
    torrent_id = request.match_info.get('id', None)
    torrent_name = request.match_info.get('name', None)
    if not tracker or not torrent_id or not torrent_name:
        return web.HTTPNotFound()
    logger.debug("Sonarr requested torrent_id: %s - torrent_name: %s from: %s", torrent_id, torrent_name,
                 tracker['name'])

    # retrieve .torrent link for specified torrent_id (id)
    torrent_link = yield from tracker['plugin'].get_torrent_link(torrent_id, torrent_name.replace('.torrent', ''))
    if torrent_link is None:
        logger.error("Problem retrieving torrent link for: %s", torrent_id)
        return web.HTTPNotFound()

    # download .torrent
    downloaded, torrent_path = yield from download_torrent(tracker, torrent_id, torrent_link)
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


# Download torrent
@asyncio.coroutine
def download_torrent(tracker, torrent_id, torrent_link):
    chunk_size = 256 * 1024
    downloaded = False

    # generate filename
    torrents_dir = Path('torrents', tracker['name'])
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
                logger.error("Unexpected response when downloading torrent: %s from tracker: %s", torrent_link,
                             tracker.name)
                return False, None

    except Exception as ex:
        logger.exception("Exception downloading torrent: %s to %s", torrent_link, torrent_file)
        return False, None

    finally:
        downloaded = True

    logger.debug("Downloaded: %s", torrent_file)
    return downloaded, torrent_path


# Initialize torrent server
app = web.Application()
app.router.add_route('GET',
                     '/{tracker}/{id}/{name}',
                     route)

############################################################
# IRC Announce Channel Watcher
############################################################
BotBase = pydle.featurize(pydle.features.RFC1459Support, pydle.features.TLSSupport)


class IRC(BotBase):
    tracking = None

    def set_tracker(self, track):
        self.tracking = track

    def on_connect(self):
        logger.info("Connected to: %s, joining %s", self.tracking['irc_host'], self.tracking['irc_channel'])

        nick_pass = cfg["{}.nick_pass".format(self.tracking['name'].lower())]
        if nick_pass is not None and len(nick_pass) > 1:
            self.rawmsg('NICKSERV', 'IDENTIFY', cfg["{}.nick_pass".format(self.tracking['name'].lower())])

        self.join(self.tracking['irc_channel'])

    def on_message(self, source, target, message):
        global loop

        if source[0] != '#':
            logger.debug("%s sent us a message: %s", target, message)
        else:
            asyncio.run_coroutine_threadsafe(self.tracking['plugin'].parse(message), loop)

    def on_invite(self, channel, by):
        if channel == self.tracking['irc_channel']:
            self.join(self.tracking['irc_channel'])


@concurrent.threaded
def start_irc():
    global cfg

    pool = pydle.ClientPool()
    for tracker in trackers.loaded:
        logger.info("Pooling server: %s:%d %s", tracker['irc_host'], tracker['irc_port'], tracker['irc_channel'])

        nick = cfg["{}.nick".format(tracker['name'].lower())]
        client = IRC(nick)

        client.set_tracker(tracker)
        try:
            pool.connect(client, hostname=tracker['irc_host'], port=tracker['irc_port'],
                         tls=tracker['irc_tls'], tls_verify=tracker['irc_tls_verify'])
        except Exception as ex:
            logger.exception("Error while connecting to: %s", tracker['irc_host'])

    pool.handle_forever()


############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    logger.info("Starting...")
    start_irc()
    web.run_app(app, host=cfg['server.host'], port=int(cfg['server.port']))

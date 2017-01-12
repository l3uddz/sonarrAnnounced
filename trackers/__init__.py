import asyncio
import logging
from pathlib import Path

from aiohttp import web, ClientSession, FileSender
from pluginbase import PluginBase

import utils

logger = logging.getLogger("TRACKERS")
logger.setLevel(logging.DEBUG)


class Trackers(object):
    loop = None
    plugin_base = None
    source = None
    loaded = []

    def __init__(self, loop):
        self.loop = loop
        self.plugin_base = PluginBase(package='trackers')
        self.source = self.plugin_base.make_plugin_source(
            searchpath=['./trackers'],
            identifier='trackers')

        # Load all trackers
        logger.info("Loading trackers...")

        for tmp in self.source.list_plugins():
            tracker = self.source.load_plugin(tmp)
            loaded = self.loop.run_until_complete(tracker.init())
            if loaded:
                logger.info("Initialized tracker: %s", tracker.name)

                self.loaded.append({
                    'name': tracker.name.lower(), 'irc_host': tracker.irc_host,
                    'irc_port': tracker.irc_port, 'irc_channel': tracker.irc_channel, 'irc_tls': tracker.irc_tls,
                    'irc_tls_verify': tracker.irc_tls_verify, 'plugin': tracker
                })
            else:
                logger.info("Problem initializing tracker: %s", tracker.name)

    def get_tracker(self, name):
        if len(self.loaded) < 1:
            logger.debug("No trackers loaded...")
            return None

        tracker = utils.find_tracker(self.loaded, 'name', name.lower())
        if tracker is not None:
            return tracker

        return None

    ############################################################
    # Trackers Endpoint for Sonarr
    ############################################################
    @asyncio.coroutine
    def route(self, request):
        tracker = self.get_tracker(request.match_info.get('tracker', None))
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
        downloaded, torrent_path = yield from self.download_torrent(tracker, torrent_id, torrent_link)
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
    def download_torrent(self, tracker, torrent_id, torrent_link):
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

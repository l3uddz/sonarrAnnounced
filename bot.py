import asyncio
import logging

import pydle
from aiohttp import web
from deco import *
from pluginbase import PluginBase

import config

logging.basicConfig(filename="status.log",
                    format='%(asctime)s - %(name)-20s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("BOT")
logger.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()

############################################################
# Configuration
############################################################

cfg = config.init()


############################################################
# Classes
############################################################
class Trackers(object):
    plugin_base = None
    source = None
    loaded = []

    def __init__(self):
        self.plugin_base = PluginBase(package='trackers')
        self.source = self.plugin_base.make_plugin_source(
            searchpath=['./trackers'],
            identifier='trackers')

        # Load all trackers
        logger.info("Loading trackers...")

        for tmp in self.source.list_plugins():
            tracker = self.source.load_plugin(tmp)
            loaded = loop.run_until_complete(tracker.init())
            if loaded:
                logger.info("Initialized tracker: %s", tracker.name)

                self.loaded.append({
                    'name': tracker.name, 'irc_host': tracker.irc_host,
                    'irc_port': tracker.irc_port, 'irc_channel': tracker.irc_channel, 'irc_tls': tracker.irc_tls,
                    'irc_tls_verify': tracker.irc_tls_verify, 'plugin': tracker
                })
            else:
                logger.info("Problem initializing tracker: %s", tracker.name)


############################################################
# Initializers
############################################################
# Load trackers
trackers = Trackers()
if len(trackers.loaded) <= 0:
    logger.info("No trackers were initialized, exiting...")
    quit()

# Load torrent server, add tracker routing points
app = web.Application()
for track in trackers.loaded:
    app.router.add_route('GET',
                         '/{}/'.format(track['name'].lower()) + '{id}/{name}',
                         track['plugin'].route)
    logger.info("Added tracker route: '/%s/'", track['name'].lower())

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

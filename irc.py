import logging
import socket

import pydle
from deco import *

import config

BotBase = pydle.featurize(pydle.features.RFC1459Support, pydle.features.TLSSupport)

logger = logging.getLogger("IRC")
logger.setLevel(logging.DEBUG)

cfg = config.init()


class IRC(BotBase):
    tracking = None

    # temp fix until pydle handles connect failures
    def connect(self, *args, **kwargs):
        try:
            super().connect(*args, **kwargs)
        except socket.error:
            self.on_disconnect(expected=False)

    def set_tracker(self, track):
        self.tracking = track

    def on_connect(self):
        logger.info("Connected to: %s, joining %s", self.tracking['irc_host'], self.tracking['irc_channel'])

        nick_pass = cfg["{}.nick_pass".format(self.tracking['name'].lower())]
        if nick_pass is not None and len(nick_pass) > 1:
            self.rawmsg('NICKSERV', 'IDENTIFY', cfg["{}.nick_pass".format(self.tracking['name'].lower())])

        self.join(self.tracking['irc_channel'])

    def on_message(self, source, target, message):
        if source[0] != '#':
            logger.debug("%s sent us a message: %s", target, message)
        else:
            self.tracking['plugin'].parse(message)

    def on_invite(self, channel, by):
        if channel == self.tracking['irc_channel']:
            self.join(self.tracking['irc_channel'])


@concurrent.threaded
def start_irc(trackers):
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

import asyncio
import logging

from aiohttp import web

import config
import irc
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

# Torrent server
app = web.Application()
app.router.add_route('GET',
                     '/{tracker}/{id}/{name}',
                     trackers.route)

############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    irc.start_irc(trackers, loop)
    web.run_app(app, host=cfg['server.host'], port=int(cfg['server.port']))

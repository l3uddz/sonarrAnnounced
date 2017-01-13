import logging

import config
import irc
import webui
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

# Trackers
trackers = Trackers()
if len(trackers.loaded) <= 0:
    logger.info("No trackers were initialized, exiting...")
    quit()

############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    irc.start_irc(trackers)
    webui.run()

import logging
from time import sleep

from worker import Worker

import irc
import webui
from trackers import Trackers

thread_irc = None
thread_webui = None
trackers = None
logger = logging.getLogger("MANAGER")
logger.setLevel(logging.DEBUG)


def run():
    global thread_irc, thread_webui, trackers

    trackers = Trackers()
    if len(trackers.loaded) <= 0:
        logger.info("No trackers were initialized, exiting...")
        quit()

    thread_irc = irc_task(trackers)
    thread_webui = webui_task(trackers)

    thread_irc.fire('START')
    thread_webui.fire('START')

    thread_irc.wait_thread(thread_irc)
    thread_webui.wait_thread(thread_webui)

    logger.debug("Finished waiting for irc & webui threads")


############################################################
# Tasks
############################################################

def irc_task(trackers):
    worker = Worker()
    working = True

    @worker.listen("START")
    def _(event):
        logger.debug("Start IRC Task signaled")
        while working:
            try:
                irc.start(trackers)
            except Exception as e:
                logger.exception("Exception irc_task START: ")

            sleep(30)

        logger.debug("IRC Task finished")

    return worker.start()


def webui_task(trackers):
    worker = Worker()
    working = True

    @worker.listen("START")
    def _(event):
        logger.debug("Start WebUI Task signaled")
        while working:
            try:
                webui.run(trackers)
            except Exception as e:
                logger.exception("Exception webui_task START: ")

            sleep(30)

        logger.debug("WebUI Task finished")

    return worker.start()

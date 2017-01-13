import logging

from blinker import Signal

logger = logging.getLogger("MANAGER")
logger.setLevel(logging.DEBUG)

signal_shutdown = Signal()
signal_restart = Signal()
signal_config_change = Signal()


@signal_shutdown.connect
def shutdown(sender, **kw):
    logger.debug("shutdown signaled")


@signal_restart.connect
def connect(sender, **kw):
    logger.debug("restart signaled")


@signal_config_change.connect
def config_change(sender, **kw):
    logger.debug("config_change signaled")

import logging

import profig

logger = logging.getLogger("CONFIG")
cfg = profig.Config('settings.cfg')


def init():
    global cfg

    cfg.init('server.host', 'localhost')
    cfg.init('server.port', '8080')
    cfg.init('bot.nickname', '%USER%_autodl')
    cfg.init('sonarr.apikey', '')
    cfg.init('sonarr.url', 'http://localhost:8989')
    cfg.init('iptorrents.user', '')
    cfg.init('iptorrents.auth_key', '')
    cfg.init('iptorrents.torrent_pass', '')
    cfg.init('morethan.user', '')
    cfg.init('morethan.auth_key', '')
    cfg.init('morethan.torrent_pass', '')

    cfg.sync()
    return cfg

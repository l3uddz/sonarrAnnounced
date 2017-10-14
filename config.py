import profig

cfg = profig.Config('settings.cfg')


def init():
    global cfg

    # Settings
    cfg.init('server.host', 'localhost')
    cfg.init('server.port', '3467')
    cfg.init('server.user', 'admin')
    cfg.init('server.pass', 'password')

    cfg.init('sonarr.apikey', '')
    cfg.init('sonarr.url', 'http://localhost:8989')

    cfg.init('bot.debug_file', True)
    cfg.init('bot.debug_console', True)

    # Trackers
    cfg.init('iptorrents.nick', '')
    cfg.init('iptorrents.nick_pass', '')
    cfg.init('iptorrents.auth_key', '')
    cfg.init('iptorrents.torrent_pass', '')

    cfg.init('morethan.nick', '')
    cfg.init('morethan.nick_pass', '')
    cfg.init('morethan.auth_key', '')
    cfg.init('morethan.torrent_pass', '')

    cfg.init('btn.nick', '')
    cfg.init('btn.nick_pass', '')
    cfg.init('btn.auth_key', '')
    cfg.init('btn.torrent_pass', '')

    cfg.init('nbl.nick', '')
    cfg.init('nbl.nick_pass', '')
    cfg.init('nbl.auth_key', '')
    cfg.init('nbl.torrent_pass', '')

    cfg.init('hdtorrents.nick', '')
    cfg.init('hdtorrents.nick_pass', '')
    cfg.init('hdtorrents.cookies', '')

    cfg.init('xspeeds.nick', '')
    cfg.init('xspeeds.nick_pass', '')
    cfg.init('xspeeds.torrent_pass', '')

    cfg.init('flro.nick', '')
    cfg.init('flro.nick_pass', '')
    cfg.init('flro.torrent_pass', '')

    cfg.sync()
    return cfg

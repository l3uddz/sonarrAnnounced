import asyncio
import datetime
import logging

from aiohttp import ClientSession

import config

logger = logging.getLogger("SONARR")
logger.setLevel(logging.DEBUG)
cfg = config.init()


@asyncio.coroutine
def wanted(title, download_link, indexer):
    global cfg

    approved = False
    logger.debug("Notifying Sonarr of release from %s: %s @ %s", indexer, title, download_link)

    headers = {'X-Api-Key': cfg['sonarr.apikey']}
    params = {
        'title': title,
        'downloadUrl': download_link,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat(),
        'indexer': indexer
    }

    with ClientSession(headers=headers) as session:
        req = yield from session.post(url="{}/api/release/push".format(cfg['sonarr.url']), params=params)
        resp = yield from req.json()

        if 'approved' in resp:
            approved = resp['approved']

    return approved

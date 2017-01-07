import logging
import re

from libs import bencode

logger = logging.getLogger("UTILS")


#############################################################
# Useful reusable methods
#############################################################
def validate_torrent(torrent_file):
    validated = False

    try:
        with torrent_file.open('rb') as torrent:
            torrent_data = torrent.read()

        torrent = bencode.decode(torrent_data)
        validated = True

    except Exception as ex:
        logger.exception("Exception while validate_torrent:")

    return validated


def get_id(text, group=0):
    torrent_id = None
    try:
        m = re.findall('id=(\S*)', text)
        if m:
            torrent_id = m[group]

    except Exception as ex:
        logger.exception("Exception while get_id:")

    return torrent_id


def substr(data, first, last, strip):
    val = None
    try:
        if strip:
            val = data[data.find(first) + len(first):data.find(last)]
        else:
            val = data[data.find(first):data.find(last) + len(last)]

    except Exception as ex:
        logger.exception("Exception while substr:")

    return val


def str_before(data, before):
    val = None
    try:
        val = data[0:data.find(before) - 1]
    except Exception as ex:
        logger.exception("Exception while str_before:")

    return val


def get_urls(text):
    return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)


def strip_irc_color_codes(line):
    line = re.sub("\x03\d\d?,\d\d?", "", line)
    line = re.sub("\x03\d\d?", "", line)
    line = re.sub("[\x01-\x1F]", "", line)
    return line

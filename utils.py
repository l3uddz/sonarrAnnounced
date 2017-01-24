import logging
import re

from unidecode import unidecode

logger = logging.getLogger("UTILS")


#############################################################
# Useful reusable methods
#############################################################

def get_id(text, group=1, pattern=None):
    torrent_id = None
    try:
        if pattern is not None:
            m = re.search(pattern, text)
            if m:
                torrent_id = m.group(group)
        else:
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


# credits: http://stackoverflow.com/a/4391978
def find_tracker(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return dic
    return None


def replace_spaces(text, new):
    return re.sub('[ ]{1,}', new, text)


def formatted_torrent_name(torrent_name):
    chars = {
        # strip chars
        '?': '',
        "'": '',
        '\\': '',
        '/': '',
        ':': '',
        ';': '',
        # replace chars
        '@': 'at.',
        '&': 'and.'
    }

    formatted = unidecode(torrent_name)
    for look, replace in chars.items():
        formatted = formatted.replace(look, replace)

    # replace date hypons with .'s (some release titles will have - in it, e.g. Hawaii.Five-O.S01E01...)
    date_pattern = '(\d{4}-\d{2}-\d{2})'
    m = re.search(date_pattern, formatted)
    if m:
        formatted = formatted.replace(m.group(0), m.group(0).replace('-', '.'))

    return formatted

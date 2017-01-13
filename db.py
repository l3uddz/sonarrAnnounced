import logging

from pony.orm import *

logger = logging.getLogger("DB")
logger.setLevel(logging.DEBUG)

db = Database()


class Announced(db.Entity):
    title = Required(str)
    indexer = Required(str)


class Snatched(db.Entity):
    title = Required(str)
    indexer = Required(str)


db.bind('sqlite', 'brain.db', create_db=True)
db.generate_mapping(create_tables=True)

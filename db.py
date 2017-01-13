import logging

from peewee import *

logger = logging.getLogger("DB")
logger.setLevel(logging.DEBUG)

db = SqliteDatabase('brain.db', threadlocals=True)


class Announced(Model):
    title = CharField()
    indexer = CharField()

    class Meta:
        database = db


class Snatched(Model):
    title = CharField()
    indexer = CharField()

    class Meta:
        database = db


db.connect()
db.create_tables([Announced, Snatched], safe=True)

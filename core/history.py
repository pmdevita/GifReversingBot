# Manage a database of the last few months reverses and their links in order to save time
from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit

from core.gif import Gif as Gif_object

db = Database()

"""
v1 Database
CREATE TABLE "gif" (
  "id" INTEGER CONSTRAINT "pk_gif" PRIMARY KEY AUTOINCREMENT,
  "origin_host" INTEGER NOT NULL,
  "origin_id" TEXT NOT NULL,
  "reversed_host" INTEGER NOT NULL,
  "reversed_id" TEXT NOT NULL,
  "time" DATE
)

v2 Database
CREATE TABLE "gif" (
  "id" INTEGER CONSTRAINT "pk_gif" PRIMARY KEY AUTOINCREMENT,
  "origin_host" INTEGER NOT NULL,
  "origin_id" TEXT NOT NULL,
  "reversed_host" INTEGER NOT NULL,
  "reversed_id" TEXT NOT NULL,
  "time" DATE NOT NULL,
  "nsfw" BOOLEAN NOT NULL
)

"""



class Gif(db.Entity):
    id = PrimaryKey(int, auto=True)
    origin_host = Required(int)
    origin_id = Required(str)
    reversed_host = Required(int)
    reversed_id = Required(str)
    time = Required(date)
    nsfw = Optional(bool)

# Use MariaDB?
db.bind(provider='sqlite', filename='../database.sqlite', create_db=True)

db.generate_mapping(create_tables=True)


def check_database(original_gif):
    # Have we reversed this gif before?
    with db_session:
        query = select(g for g in Gif if g.origin_host == original_gif.host and g.origin_id == original_gif.id)
        gif = query.first()
    # If we have, get it's host and id
    if gif:
        host = gif.reversed_host
        id = gif.reversed_id
    # If this is not a gif we have reversed before, perhaps this is a re-reverse?
    else:
        with db_session:
            query = select(g for g in Gif if g.reversed_host == original_gif.host and g.reversed_id == original_gif.id)
            gif = query.first()
        if gif:
            host = gif.origin_host
            id = gif.origin_id
    if gif:
        print("Found in database!", gif.origin_id, gif.reversed_id)
        return Gif_object(host, id, nsfw=gif.nsfw)
    return None



def add_to_database(original_gif, reversed_gif):
    with db_session:
        new_gif = Gif(origin_host=original_gif.host, origin_id=original_gif.id, reversed_host=reversed_gif.host,
                      reversed_id=reversed_gif.id, time=date.today(), nsfw=original_gif.nsfw)
        commit()





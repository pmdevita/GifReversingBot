# Manage a database of the last few months reverses and their links in order to save time
from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit

from core.gif import Gif as Gif_object

db = Database()


class Gif(db.Entity):
    id = PrimaryKey(int, auto=True)
    origin_host = Required(int)
    origin_id = Required(str)
    reversed_host = Required(int)
    reversed_id = Required(str)
    time = Optional(date)

# Use MariaDB?
db.bind(provider='sqlite', filename='../database.sqlite', create_db=True)

db.generate_mapping(create_tables=True)


def check_database(original_gif):
    # Have we reversed this gif before?
    with db_session:
        query = select(g for g in Gif if g.origin_host == original_gif.host and g.origin_id == original_gif.id)
        gif = query.first()
    if gif:
        print("Found in database!", gif.origin_id, gif.reversed_id)
        return Gif_object(gif.reversed_host, gif.reversed_id)
    # Is it a gif that we made?
    with db_session:
        query = select(g for g in Gif if g.reversed_host == original_gif.host and g.reversed_id == original_gif.id)
        gif = query.first()
    if gif:
        print("Found in database!", gif.origin_id, gif.reversed_id)
        return Gif_object(gif.origin_host, gif.origin_id)
    return None



def add_to_database(original_gif, reversed_gif):
    with db_session:
        new_gif = Gif(origin_host=original_gif.host, origin_id=original_gif.id, reversed_host=reversed_gif.host,
                      reversed_id=reversed_gif.id, time=date.today())
        commit()





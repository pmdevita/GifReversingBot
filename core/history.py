# Manage a database of the last few months reverses and their links in order to save time
from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit

from core.gif import Gif as Gif_object
from core.credentials import CredentialsLoader

db = Database()

def bind_db(db):
    creds = CredentialsLoader.get_credentials()['database']

    if creds['type'] == 'sqlite':
        db.bind(provider='sqlite', filename='../database.sqlite', create_db=True)
    elif creds['type'] == 'mysql':
        # Check for SSL arguments
        ssl = {}
        if creds.get('ssl-ca', None):
            ssl['ssl'] = {'ca': creds['ssl-ca'], 'key': creds['ssl-key'], 'cert': creds['ssl-cert']}

        db.bind(provider="mysql", host=creds['host'], user=creds['username'], password=creds['password'],
                db=creds['database'], ssl=ssl, port=int(creds.get('port', 3306)))
    else:
        raise Exception("No database configuration")

    db.generate_mapping(create_tables=True)


class Gif(db.Entity):
    id = PrimaryKey(int, auto=True)
    origin_host = Required(int)
    origin_id = Required(str)
    reversed_host = Required(int)
    reversed_id = Required(str)
    time = Required(date)
    nsfw = Optional(bool)
    total_requests = Optional(int)
    last_requested_date = Optional(date)


bind_db(db)


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
            query = select(g for g in Gif if g.reversed_host == original_gif.host and g.reversed_id == original_gif.id)
            gif = query.first()
            if gif:
                host = gif.origin_host
                id = gif.origin_id
        if gif:
            print("Found in database!", gif.origin_id, gif.reversed_id)
            gif.last_requested_date = date.today()
            gif.total_requests += 1
            return Gif_object(host, id, nsfw=gif.nsfw)
    return None



def add_to_database(original_gif, reversed_gif):
    with db_session:
        new_gif = Gif(origin_host=original_gif.host, origin_id=original_gif.id, reversed_host=reversed_gif.host,
                      reversed_id=reversed_gif.id, time=date.today(), nsfw=original_gif.nsfw, total_requests=1,
                      last_requested_date=date.today())
        commit()





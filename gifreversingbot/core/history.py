# Manage a database of the last few months reverses and their links in order to save time
from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, Set

from gifreversingbot.core.gif import GifHostManager
from gifreversingbot.hosts import Gif as NewGif_object, GifHost
from gifreversingbot.core.credentials import CredentialsLoader

db = Database()


def bind_db(db):
    creds = CredentialsLoader.get_credentials()['database']

    if creds['type'] == 'sqlite':
        db.bind(provider='sqlite', filename='../../database.sqlite', create_db=True)
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


class GifHosts(db.Entity):
    name = PrimaryKey(str)
    origin_gifs = Set('Gif', reverse='origin_host')
    reversed_gifs = Set('Gif', reverse='reversed_host')


class Gif(db.Entity):
    id = PrimaryKey(int, auto=True)
    origin_host = Required(GifHosts, reverse='origin_gifs')
    origin_id = Required(str)
    reversed_host = Required(GifHosts, reverse='reversed_gifs')
    reversed_id = Required(str)
    time = Required(date)
    nsfw = Optional(bool)
    total_requests = Optional(int)
    last_requested_date = Optional(date)


bind_db(db)

ghm = GifHostManager()


def sync_hosts():
    # Double check gifhost bindings
    with db_session:
        for host in ghm.hosts:
            q = select(h for h in GifHosts if h.name == host.name).first()
            if not q:
                new = GifHosts(name=host.name)


sync_hosts()


def check_database(original_gif: NewGif_object):
    # Have we reversed this gif before?
    with db_session:
        host = GifHosts[original_gif.host.name]
        gif_id = original_gif.id
        if original_gif.host.name == "LinkGif":
            if len(gif_id) > 255:
                original_gif.id = original_gif.id[:255]
        query = select(g for g in Gif if g.origin_host == host and
                       g.origin_id == gif_id)
        gif = query.first()
        # If we have, get it's host and id
        if gif:
            host = gif.reversed_host
            id = gif.reversed_id
        # If this is not a gif we have reversed before, perhaps this is a re-reverse?
        else:
            query = select(g for g in Gif if g.reversed_host == host and
                           g.reversed_id == original_gif.id)
            gif = query.first()
            if gif:
                host = gif.origin_host
                id = gif.origin_id
        if gif:
            print("Found in database!", gif.origin_id, gif.reversed_id)
            gif.last_requested_date = date.today()
            gif.total_requests += 1
            return ghm.host_names[host.name].get_gif(id, nsfw=gif.nsfw)
    return None


def add_to_database(original_gif, reversed_gif):
    with db_session:
        # Extra checks for linkgif
        if original_gif.host.name == "LinkGif":
            if len(original_gif.id) > 255:
                original_gif.id = original_gif.id[:255]
        new_gif = Gif(origin_host=GifHosts[original_gif.host.name], origin_id=original_gif.id,
                         reversed_host=GifHosts[reversed_gif.host.name], reversed_id=reversed_gif.id, time=date.today(),
                         nsfw=original_gif.nsfw, total_requests=1, last_requested_date=date.today())


def delete_from_database(original_gif):
    with db_session:
        # Select gif as original first
        query = select(g for g in Gif if g.origin_host == GifHosts[original_gif.host.name] and
                       g.origin_id == original_gif.id)
        gif = query.first()
        # If we have it, delete it
        if gif:
            gif.delete()
        # Possibly a rereversed then
        else:
            query = select(g for g in Gif if g.reversed_host == GifHosts[original_gif.host.name] and
                           g.reversed_id == original_gif.id)
            gif = query.first()
            if gif:
                gif.delete()


def list_by_oldest_access(reversed_host: GifHost, cutoff):
    with db_session:
        query = select(g for g in Gif if g.reversed_host == GifHosts[reversed_host.name]
                       and g.last_requested_date < cutoff).order_by(Gif.last_requested_date)

        print(query)
        return query[:]


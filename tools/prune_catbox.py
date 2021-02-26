# Add project root folder to python path
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

import praw
import datetime
from pprint import pprint
from core import constants as consts
from core.credentials import CredentialsLoader
from core.gif import GifHostManager
from core.history import check_database, add_to_database, delete_from_database, list_by_oldest_access

CUTOFF = datetime.date.today() - datetime.timedelta(weeks=9*4)

print(CUTOFF)

credentials = CredentialsLoader().get_credentials()

# Only needed to initialize ghm
reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])


ghm = GifHostManager(reddit)
catbox = ghm.host_names['Catbox']

gifs = list_by_oldest_access(catbox, CUTOFF)
print(len(gifs))
print(gifs[0].reversed_id, gifs[0].last_requested_date)

for gif in gifs:
    catbox_gif = catbox.get_gif(id=gif.reversed_id)
    catbox.delete(catbox_gif)
    delete_from_database(catbox_gif)





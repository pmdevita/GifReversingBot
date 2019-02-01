import praw
import prawcore
import time
import traceback
from core.credentials import CredentialsLoader
from core.regex import REPatterns
from core import constants as consts
from core.secret import secret_process
from core.context import extract_gif_from_comment

from pprint import pprint
import json
import datetime
from collections import defaultdict
from core.gif import GifHostManager

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])


def get_date(seconds):
    return datetime.datetime.utcfromtimestamp(seconds).\
        replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


print("GifReversingBot Statistics v{} Ctrl+C to stop".format(consts.version))

ghm = GifHostManager(reddit)
counter = 0
users = defaultdict(int)
karma = {}
gifs = {}

for comment in reddit.user.me().comments.new(limit=None):
    counter += 1
    author = comment.parent().author
    print(counter, comment.id, author, extract_gif_from_comment(ghm, comment.body), get_date(comment.created_utc))
    if author:
        users[author.name] += 1
    # pprint(vars(comment))
    karma[comment.id] = comment.ups - comment.downs

    # if not counter % 200:
    #     input()

with open('stats.json', 'w') as f:
    json.dump({'users': users, 'upvotes': karma}, f)

import praw
import datetime
import pony
from core.credentials import CredentialsLoader
from core import constants as consts
from core.gif import GifHostManager
from core.regex import REPatterns

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

ghm = GifHostManager(reddit)

print(f"{consts.bot_name} Console v{consts.version}")





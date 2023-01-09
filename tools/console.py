import praw
from gifreversingbot.core.credentials import CredentialsLoader
from gifreversingbot.core import constants as consts
from gifreversingbot.core.gif import GifHostManager

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





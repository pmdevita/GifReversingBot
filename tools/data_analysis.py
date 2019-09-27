import praw
import psaw
import datetime
import pony
from core.credentials import CredentialsLoader
from core import constants as consts

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

ps = PushshiftAPI(reddit)

print("GifReversingBot Data Analysis v{} Ctrl+C to stop".format(consts.version))

start = int(dt.datetime(2018, 9, 16).timestamp())
end = int(dt.datetime(2019, 9, 14).timestamp())




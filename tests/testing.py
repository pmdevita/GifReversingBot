import praw
from gifreversingbot.core.credentials import CredentialsLoader
from gifreversingbot.core import constants as consts
from gifreversingbot.core.context import CommentContext
from gifreversingbot.core.gif import GifHostManager

"""These tests rely on comments on in my test subreddit so they'll need some work for other people to use"""


credentials = CredentialsLoader().get_credentials()

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])
ghm = GifHostManager(reddit)

context = CommentContext(reddit, reddit.comment('eomsgqq'), ghm)
print(vars(context))
#
# gif = ghm.host_names['Gfycat'].get_gif(text="https://gfycat.com/SkeletalShallowArmadillo")
# gif.analyze()

import unittest
import praw
from core.credentials import CredentialsLoader
from core import constants as consts
from core.gif import GifHostManager

"""These tests rely on comments on in my test subreddit so they'll need some work for other people to use"""


credentials = CredentialsLoader().get_credentials()

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

ghm = GifHostManager(reddit=reddit)

# Assert subset of dict is deprecated soooo....
def extractDictAFromB(A,B):
    return dict([(k,B[k]) for k in A.keys() if k in B.keys()])

class GHLTests(unittest.TestCase):
    def test_reddit(self):
        # Self posts should not end in infinite recursion
        self.assertIsNone(ghm.extract_gif(text="https://www.reddit.com/user/GifReversingBot/comments/b44fkn/how_to_use_gifreversingbot"))


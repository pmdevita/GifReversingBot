import unittest
import praw
from core.credentials import CredentialsLoader
from core import constants as consts
from core.context import CommentContext

"""These tests rely on comments on in my test subreddit so they'll need some work for other people to use"""


credentials = CredentialsLoader().get_credentials()

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

# Assert subset of dict is deprecated soooo....
def extractDictAFromB(A,B):
    return dict([(k,B[k]) for k in A.keys() if k in B.keys()])

class ContextTests(unittest.TestCase):
    def test_normal(self):
        correct = {'comment': 't1_ekf4i80', 'rereverse': False, 'unnecessary_manual': False, 'nsfw': False,
                   'distinguish': False, 'reupload': False, 'url': 'https://imgur.com/5PVtWsf.gifv'}
        comment = reddit.comment('ekf4i80')
        context = CommentContext(reddit, comment)
        obj = context.to_json()
        print(obj)
        self.assertEqual(correct, extractDictAFromB(correct, obj))

    def test_nsfw_keyword(self):
        correct = {'comment': 't1_ekf5cl8', 'nsfw': True, 'url': 'https://imgur.com/5PVtWsf.gifv'}
        comment = reddit.comment('ekf5cl8')
        context = CommentContext(reddit, comment)
        obj = context.to_json()
        print(obj)
        self.assertEqual(correct, extractDictAFromB(correct, obj))

    def test_nsfw_post(self):
        correct = {'comment': 't1_ekf25nx', 'nsfw': True, 'url': 'https://imgur.com/Xo73bxR.gifv'}
        comment = reddit.comment('ekf25nx')
        context = CommentContext(reddit, comment)
        obj = context.to_json()
        print(obj)
        self.assertEqual(correct, extractDictAFromB(correct, obj))

    def test_nsfw_sub(self):
        sub = reddit.subreddit('pmdevita')
        sub.mod.update(over_18=True)
        correct = {'comment': 't1_ekf4i80', 'nsfw': True, 'url': 'https://imgur.com/5PVtWsf.gifv'}
        comment = reddit.comment('ekf4i80')
        context = CommentContext(reddit, comment)
        obj = context.to_json()
        print(obj)
        sub.mod.update(over_18=False)
        self.assertEqual(correct, extractDictAFromB(correct, obj))

    def test_nsfw_post2(self):
        def test_nsfw_keyword(self):
            correct = {'comment': 't1_ekyb5cv', 'nsfw': True, 'url': 'https://i.redd.it/ykr4josxacs21.gif'}
            comment = reddit.comment('ekyb5cv')
            context = CommentContext(reddit, comment)
            obj = context.to_json()
            print(obj)
            self.assertEqual(correct, extractDictAFromB(correct, obj))
import praw.models
from core import parse
from core import constants as consts
from core.regex import REPatterns

REREVERSE = 1

class CommentContext:
    def __init__(self, comment):
        self.comment = comment
        self.rereverse = False
        self.context = self._determine_target_url(self.comment)

    def _determine_target_url(self, reddit_object):
        """Recursively find the gif URL the user wants"""
        # If the object is a post, check it's URL
        if isinstance(reddit_object, praw.models.Submission):
            # If post is a text post, search it's content
            if reddit_object.is_self:
                # Check every word to see if it matches a URL
                for i in reddit_object.selftext.split():
                    if parse.validate_url(i):
                        self.url = i
                        return reddit_object
            # If the post is a link post, check it's URL
            else:
                if parse.validate_url(reddit_object.url):
                    self.url = reddit_object.url
                    return reddit_object
                else:
                    return None
        # If the object is a comment, check it's text
        elif isinstance(reddit_object, praw.models.Comment):
            if reddit_object.author == consts.username: # Someone is trying to rereverse
                self.rereverse = True
                return self._determine_target_url(reddit_object.parent())
            # Look through every word to see if one is a url
            for i in reddit_object.body.split():
                if parse.validate_url(i):
                    self.url = i
                    return reddit_object
            # Check markdown links too
            for i in REPatterns.link.findall(reddit_object.body):
                if parse.validate_url(i):
                    self.url = i
                    return reddit_object
            # We didn't find a gif, go up a level
            return self._determine_target_url(reddit_object.parent())
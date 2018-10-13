import praw.models
from core import parse
from core import constants as consts
from core.regex import REPatterns

from pprint import pprint


class CommentContext:
    def __init__(self, comment):
        """Determine the context of a summon by grabbing what comment/submission and url it is referring too"""
        self.comment = comment
        self.rereverse = False
        self.nsfw = is_nsfw(comment)
        self.context = self._determine_target_url(self.comment)

    def _determine_target_url(self, reddit_object):
        """Recursively find the gif URL the user wants"""
        # If the object is a post, check it's URL
        if isinstance(reddit_object, praw.models.Submission):
            # If post is a text post, search it's content
            if reddit_object.is_self:
                # Search text for URL
                url = find_url(reddit_object.selftext)
                # If found
                if url:
                    # Return it
                    self.url = url
                    return reddit_object
            # Else if the post is a link post, check it's URL
            else:
                if parse.validate_url(reddit_object.url):
                    self.url = reddit_object.url
                    return reddit_object
                else:
                    return None
        # Else if the object is a comment, check it's text
        elif isinstance(reddit_object, praw.models.Comment):
            # If the comment was made by the bot, it must be a rereverse request
            # If the rereverse flag is already set, we must be at least a loop deep
            if reddit_object.author == consts.username and not self.rereverse:
                self.rereverse = True
                return self._determine_target_url(reddit_object.parent())
            # Search text for URL
            url = find_url(reddit_object.body)
            # If found
            if url:
                # Return it
                self.url = url
                return reddit_object
            # We didn't find a gif, go up a level
            return self._determine_target_url(reddit_object.parent())


def find_url(text):
    """Checks a string for valid urls"""
    # Look through every word to see if one is a url
    for i in text.split():
        if parse.validate_url(i):
            return i
    # Check markdown links too
    for i in REPatterns.link.findall(text):
        if parse.validate_url(i):
            return i
    return None


# Works but will mark a sfw gif first posted in an nsfw sub as nsfw ¯\_(ツ)_/¯
def is_nsfw(comment):
    # Identify if submission is nsfw
    post_nsfw = comment.submission.over_18

    # Why no underscore
    sub_nsfw = comment.subreddit.over18
    # print("nsfw", post_nsfw, sub_nsfw)
    return post_nsfw or sub_nsfw

if __name__ == '__main__':
    find_url("""Here is your gif!
https://gfycat.com/SneakyPeacefulAltiplanochinchillamouse

---

^(I am a bot.) [^(Report an issue)](https://www.reddit.com/message/compose/?to=pmdevita&subject=GifReversingBot%20Issue)""")
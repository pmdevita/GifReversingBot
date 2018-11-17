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
        self.unnecessary_manual = False
        self.nsfw = is_nsfw(comment)
        self.url = self.determine_target_url(self.comment)

    def determine_target_url(self, reddit_object, layer=0, checking_manual=False):
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
                    return url
            # Else if the post is a link post, check it's URL
            else:
                if parse.validate_url(reddit_object.url):
                    return reddit_object.url
                else:
                    return None
        # Else if the object is a comment, check it's text
        elif isinstance(reddit_object, praw.models.Comment):
            # If the comment was made by the bot, it must be a rereverse request
            # If the rereverse flag is already set, we must be at least a loop deep
            if reddit_object.author == consts.username and not self.rereverse and not checking_manual:
                self.rereverse = True
                return self.determine_target_url(reddit_object.parent(), layer+1, checking_manual)
            # Search text for URL
            url = find_url(reddit_object.body)
            # If found
            if url:
                # Return it
                if layer == 0:  # If this is the summon comment
                    # Double check they didn't needlessly give us the URL again
                    next_url = self.determine_target_url(reddit_object.parent(), layer+1, True)
                    if url == next_url:
                        self.unnecessary_manual = True
                    return url
                else:
                    return url
            # We didn't find a gif, go up a level
            return self.determine_target_url(reddit_object.parent(), layer+1, checking_manual)


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

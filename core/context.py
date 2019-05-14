from typing import Optional
import praw.models
from praw.const import API_PATH
from core import parse
from core import constants as consts
from core.regex import REPatterns
from core.gif import GifHostManager
from core.hosts import GifHost
from pprint import pprint

class CommentContext:
    def __init__(self, reddit, comment, ghm):
        """Determine the context of a summon by grabbing what comment/submission and url it is referring too"""
        self.ghm = ghm
        self.comment = comment
        self.rereverse = False
        self.unnecessary_manual = False
        self.nsfw = is_nsfw(comment)
        self.distinguish = False
        self.reupload = is_reupload(comment.body)
        self.url = self.determine_target_url(reddit, self.comment)

    @classmethod
    def from_json(cls, reddit, data):
        # Skip the normal init function
        context = cls.__new__(cls)
        # Process rest of data
        for i in data:
            context.__setattr__(i, data[i])
            # Process comment differently
            if i == 'comment':
                # Get reddit object info
                params = {'id': data['comment']}
                r = reddit.get(API_PATH['info'], params=params)
                context.comment = r.children[0]

        return context

    def to_json(self):
        data = {}
        for i in vars(self):
            if i[0] != "_" or i == "comment":
                data[i] = self.__getattribute__(i)
        data['comment'] = self.comment.name
        return data



    def determine_target_url(self, reddit, reddit_object, layer=0, checking_manual=False):
        """Recursively find the gif URL the user wants"""
        # If the object is a post, check it's URL
        if isinstance(reddit_object, praw.models.Submission):
            # Running through enough levels can cause a recursion error,
            # which we need to then refresh our comment
            try:
                # Any mention of NSFW must trip the NSFW flag
                if is_nsfw_text(reddit_object.title) and not checking_manual:
                    self.nsfw = True
                # If post is a text post, search it's content
                if reddit_object.is_self:
                    # Any mention of NSFW must trip the NSFW flag
                    if is_nsfw_text(reddit_object.selftext) and not checking_manual:
                        self.nsfw = True
                    # Search text for URL
                    url = self.ghm.extract_gif(reddit_object.selftext, nsfw=self.nsfw)
                    # If found
                    if url:
                        # Return it
                        return url
                # Else if the post is a link post, check it's URL
                else:
                    url = self.ghm.extract_gif(reddit_object.url, nsfw=self.nsfw)
                    if url:
                        return url
                    else:
                        return None
            except RecursionError:
                submission = reddit.submission(id=reddit_object.id)
                return self.determine_target_url(reddit, submission, layer + 1, checking_manual)

        # Else if the object is a comment, check it's text
        elif isinstance(reddit_object, praw.models.Comment):
            # Any mention of NSFW must trip the NSFW flag
            if is_nsfw_text(reddit_object.body) and not checking_manual:
                self.nsfw = True
            # If the comment was made by the bot, it must be a rereverse request
            # If the rereverse flag is already set, we must be at least a loop deep
            if reddit_object.author == consts.username and not self.rereverse and not checking_manual \
                    and not self.reupload:
                self.rereverse = True
                return self.determine_target_url(reddit, reddit_object.parent(), layer+1, checking_manual)
            # If it's an AutoModerator summon, move our summon comment to the AutoMod's parent
            if reddit_object.author == "AutoModerator" and layer == 0:
                self.comment = reddit_object.parent()
                # Delete comment if a moderator
                modded_subs = [i.name for i in reddit.user.moderator_subreddits()]
                if reddit_object.subreddit.name in modded_subs:
                    self.determine_target_url(reddit, reddit_object.parent(), layer + 1, checking_manual)
                    if reddit_object.stickied:
                        self.distinguish = True
                    reddit_object.mod.remove()

            # Search text for URL
            url = self.ghm.extract_gif(reddit_object.body, nsfw=self.nsfw)
            # If found
            if url:
                # Return it
                if layer == 0:  # If this is the summon comment
                    # Double check they didn't needlessly give us the URL again
                    next_url = self.determine_target_url(reddit, reddit_object.parent(), layer+1, True)
                    if url == next_url:
                        self.unnecessary_manual = True
                return url
            # We didn't find a gif, go up a level
            return self.determine_target_url(reddit, reddit_object.parent(), layer+1, checking_manual)


def old_find_url(text):
    """Checks a string for valid urls"""
    # Look through every word to see if one is a url
    for i in text.split():
        if parse.old_validate_url(i):
            return i
    # Check markdown links too
    for i in REPatterns.link.findall(text):
        if parse.old_validate_url(i):
            return i
    return None


"""Deprecated???"""
def extract_gif_from_comment(ghm: GifHostManager, text: str) -> Optional[GifHost]:
    """Checks a string for valid urls"""
    # Look through every word to see if one is a url
    gif = ghm.extract_gif(text)
    if gif:
        return gif
    # Check markdown links too
    for i in REPatterns.link.findall(text):
        if ghm.extract_gif(i):
            return i
    return None


# Works but will mark a sfw gif first posted in an nsfw sub as nsfw ¯\_(ツ)_/¯
def is_nsfw(comment):
    # Identify if submission is nsfw
    if isinstance(comment, praw.models.Comment):
        post_nsfw = comment.submission.over_18
        # Why no underscore
        sub_nsfw = comment.subreddit.over18
        # print("nsfw", post_nsfw, sub_nsfw)
        return post_nsfw or sub_nsfw
    elif isinstance(comment, praw.models.Submission):
        post_nsfw = comment.over_18
        # Why no underscore
        sub_nsfw = comment.subreddit.over18
        # print("nsfw", post_nsfw, sub_nsfw)
        return post_nsfw or sub_nsfw


def is_nsfw_text(text):
    m = REPatterns.nsfw_text.findall(text)
    return len(m) != 0


def is_reupload(text):
    m = REPatterns.reupload_text.findall(text)
    return len(m) != 0

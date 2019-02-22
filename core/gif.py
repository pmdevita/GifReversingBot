from typing import Optional

import os
import importlib
from core import constants as consts
from core.hosts import GifHost, Gif
from core.regex import REPatterns

class GifHostManager:
    hosts = []
    reddit = None

    def __init__(self, reddit):
        if not self.hosts:
            # Dynamically load gif hosts
            files = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hosts"))
            for f in files:
                # __init__.py or __pycache__
                if f[:2] != "__" and f[-3:] == ".py":
                    i = importlib.import_module("." + f[:-3], 'core.hosts')
            for host in GifHost.__subclasses__():
                self.hosts.append(host)
        if not self.reddit:
            self.reddit = reddit

    def extract_gif(self, text) -> Optional[Gif]:
        for host in self.hosts:
            if host.regex.findall(text):
                return host.get_gif(url=text)
        # Try to resolve a submission URL
        if REPatterns.reddit_submission.findall(text):
            submission = self.reddit.submission(REPatterns.reddit_submission.findall(text)[0][2])
            if submission.media:
                url = submission.media['reddit_video']['fallback_url']
            else:
                url = submission.url
            return self.extract_gif(url)
        print("Unknown URL Type")
        return None


class Gif:
    def __init__(self, host, id, url=None, log=True, nsfw=False):
        self.host = host
        self.id = id
        # Do we log this gif in the db?
        self.log = log
        self.audio = False

        self.nsfw = nsfw

        if url:
            self.url = url
        elif host == consts.IMGUR:
            self.url = "https://imgur.com/{}.gifv".format(id)
        elif host == consts.GFYCAT:
            self.url = "https://gfycat.com/{}".format(id)
        elif host == consts.REDDITGIF:
            self.url = "https://i.redd.it/{}.gif".format(id)
        elif host == consts.REDDITVIDEO:
            self.url = "https://v.redd.it/{}".format(id)
            # self.audio = True
        elif host == consts.STREAMABLE:
            self.url = "https://streamable.com/{}".format(id)
            self.audio = True
        elif host == consts.LINKGIF:
            self.url = id
        else:
            self.url = None
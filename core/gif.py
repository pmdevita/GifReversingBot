from typing import Optional
from operator import itemgetter

import os
import importlib
from core import constants as consts
from core.hosts import GifHost, GifFile
from core.hosts import Gif as NewGif
from core.regex import REPatterns

class GifHostManager:
    hosts = []
    reddit = None
    vid_priority = []
    gif_priority = []
    host_names = []

    def __init__(self, reddit=None):
        if not self.hosts:
            # Dynamically load gif hosts
            files = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hosts"))
            for f in files:
                #  __init__.py or __pycache__
                if f[:2] != "__" and f[-3:] == ".py":
                    i = importlib.import_module("." + f[:-3], 'core.hosts')
            hosts = []
            for host in GifHost.__subclasses__():
                host.ghm = self
                hosts.append([host, host.priority])
            GifHostManager.hosts = [i[0] for i in sorted(hosts, key=itemgetter(1))]
            # Create the priority lists
            # vid_priority = [[i, i.vid_len_limit] for i in self.hosts if i.can_vid]
            GifHostManager.vid_priority = [i for i in sorted(GifHostManager.hosts, key=lambda x: (x.priority,
                                           x.vid_len_limit == 0, x.vid_len_limit)) if i.can_vid]
            # gif_priority = [[i, i.gif_size_limit] for i in self.hosts if i.can_gif]
            GifHostManager.gif_priority = [i for i in sorted(GifHostManager.hosts, key=lambda x: (x.priority,
                                           x.gif_size_limit == 0, x.gif_size_limit)) if i.can_gif]
            # GifHostManager.gif_priority = [i[0] for i in sorted(gif_priority, key=itemgetter(1))]
            GifHostManager.host_names = {i.name: i for i in self.hosts}
            # print("priority", self.hosts, self.vid_priority, self.gif_priority)
        if not self.reddit:
            GifHostManager.reddit = reddit

    # def host_names(self):
    #     return [i.name for i in self.hosts]

    def extract_gif(self, text, **kwargs) -> Optional[NewGif]:
        for host in self.hosts:
            if host.match(text):
                return host.get_gif(text=text, **kwargs)
        return None

    def get_upload_host(self, gif_files) -> [Optional[GifFile], Optional[GifHost]]:
        """Return a host that can suitably upload a file of these parameters"""
        if isinstance(gif_files, GifFile):
            gif_files = [gif_files]

        for gif_file in gif_files:
            if gif_file.type == consts.GIF:
                priority = self.gif_priority[:]
            else:
                priority = self.vid_priority[:]
            if gif_file.host in priority:
                priority.remove(gif_file.host)
                priority.insert(0, gif_file.host)

            for host in priority:
                if self._within_host_params(host, gif_file):
                    print("Decided to upload to", host, gif_file)
                    return gif_file, host
                else:
                    print("Not within params of host", host, gif_file)
        return None, None

    def _within_host_params(self, host: GifHost, gif_file: GifFile):
        """Determine whether a GifFile is within a GifHost's limitations"""
        # Several types of videos but only one type of gif
        # Can gif check may be redundant due to priority calculations
        if gif_file.type == consts.GIF:
            if host.can_gif and (host.gif_size_limit >= gif_file.size or host.gif_size_limit == 0) and \
               (host.gif_frame_limit >= gif_file.frames or host.gif_frame_limit == 0):
                return True
        else:
            if host.can_vid and (host.vid_len_limit >= gif_file.duration or host.vid_len_limit == 0) and \
               (host.vid_size_limit >= gif_file.size or host.vid_size_limit == 0) and \
                    (host.audio == gif_file.audio or not gif_file.audio):
                # Audio logic: if they match or if audio is false (meaning it doesn't matter)

                return True
        return False




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

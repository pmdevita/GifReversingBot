from typing import Optional, List
from operator import itemgetter

import os
import importlib
from gifreversingbot.core import constants as consts
from gifreversingbot.hosts import NO_NSFW, ONLY_NSFW, GifFile, Gif as NewGif, GifHost


class GifHostManager:
    hosts = []
    reddit = None
    vid_priority = []
    gif_priority = []
    host_names = {}

    def __init__(self, reddit=None):
        if not self.hosts:
            # Dynamically load gif hosts
            files = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../hosts"))
            for f in files:
                #  __init__.py or __pycache__
                if f[:2] != "__" and f[-3:] == ".py":
                    i = importlib.import_module("." + f[:-3], 'gifreversingbot.hosts')
            hosts = []
            for host in self._get_all_subclasses(GifHost):
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

    def _get_all_subclasses(self, parent_class):
        classes = []
        for child_class in parent_class.__subclasses__():
            classes.append(child_class)
        found_more = True
        while found_more:
            found_more = False
            for child_class in classes:
                for grandchild_class in child_class.__subclasses__():
                    if grandchild_class not in classes:
                        classes.append(grandchild_class)
                        found_more = True
        return classes

    def extract_gif(self, text, **kwargs) -> Optional[NewGif]:
        for host in self.hosts:
            if host.match(text):
                return host.get_gif(text=text, **kwargs)
        return None

    def get_upload_host(self, gif: NewGif, file: GifFile = None, ignore: Optional[List[GifHost]] = None) -> [Optional[GifFile], Optional[GifHost]]:
        """Return a host that can suitably upload a file of these parameters"""
        acceptable_files = []
        if file:
            file_list = [file]
        else:
            file_list = gif.files
        for gif_file in file_list:
            file_hosts = []
            # Create priority lists
            if gif_file.type == consts.GIF:
                priority = self.gif_priority[:]
            else:
                priority = self.vid_priority[:]

            # We prioritize the original gif host
            if gif_file.host in priority:
                priority.remove(gif_file.host)
                priority.insert(0, gif_file.host)
            if ignore:
                for gif_host in ignore:
                    priority.remove(gif_host)

            for host in priority:
                if self._within_host_params(host, gif, gif_file):
                    file_hosts.append(host)
                #     print("Decided to upload to", str(host), gif_file)
                # else:
                #     print("Not within params of host", host, gif_file)
            if file_hosts:
                acceptable_files.append({"file": gif_file, "hosts": file_hosts})
        return acceptable_files if acceptable_files else []

    def _within_host_params(self, host: GifHost, gif: NewGif, gif_file: GifFile):
        """Determine whether a GifFile is within a GifHost's limitations"""
        # Several types of videos but only one type of gif
        # Can gif check may be redundant due to priority calculations
        if (host.NSFW == NO_NSFW) and gif.nsfw:
            return False
        if (host.NSFW == ONLY_NSFW) and not gif.nsfw:
            return False

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

    def __getitem__(self, item):
        return self.host_names.get(item, None)


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

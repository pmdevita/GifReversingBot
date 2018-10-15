from core import constants as consts


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
        else:
            self.url = None
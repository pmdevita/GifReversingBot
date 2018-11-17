class GifHost:
    type = None
    regex = None
    url = None
    audio = False

    def __init__(self, context):
        self.context = context
        self.id = None
        self.get_id()

    def get_id(self):
        """Set this object's id variable to the pic's ID"""
        raise NotImplemented

    def analyze(self):
        raise NotImplemented

    def reverse(self):
        raise NotImplemented

    def upload_gif(self, gif):
        raise NotImplemented

    def upload_video(self, video):
        raise NotImplemented

    def get_gif(self):
        """Return info about the gif for checking the db"""
        if self.id:
            return Gif(self, self.id, nsfw=self.context.nsfw)
        else:
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
        elif id:
            self.url = host.url.format(id)
        else:
            self.url = None
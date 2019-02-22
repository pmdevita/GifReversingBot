class GifHost:
    name = None
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

    @classmethod
    def get_gif(cls, id=None, regex=None, url=None):
        if url:
            regex = cls.regex.findall(url)
        if regex:
            gif_id = regex[0]
        if gif_id:
            return Gif(cls, gif_id, cls.url.format(gif_id))


class Gif:
    def __init__(self, host, id, url):
        self.host = host
        self.id = id
        self.url = url

    def __repr__(self):
        return "{}-{}".format(self.host.name, self.id)
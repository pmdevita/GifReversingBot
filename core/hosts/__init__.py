import requests
from io import BytesIO
from core import constants as consts
from core.file import get_frames

class GifFile:
    def __init__(self, file, host=None, gif_type=None, size=None, duration=None, frames=0):
        self.file = file
        self.file.seek(0)
        self.type = gif_type
        self.size = None
        self.frames = frames
        if gif_type == consts.GIF and not frames:
            self.frames = get_frames(self.file)
        if size:
            self.size = size
        else:
            if isinstance(file, BytesIO):
                self.size = file.getbuffer().nbytes / 1000000
        self.duration = duration
        self.host = host


class Gif:
    process_id = False

    def __init__(self, host, id, context=None, url=None):
        self.host = host
        self.context = context

        self.pic = None
        self.file = None
        self.size = None
        self.type = None
        self.duration = None
        self.files = []

        if not self.process_id:
            self.id = id
        else:
            self.id = self._get_id()
        self.url = self.host.url_template.format(self.id)


    def __repr__(self):
        return "{}-{}".format(self.host.name, self.id)

    def _get_id(self):
        """Set this object's id variable to the pic's ID"""
        raise NotImplementedError

    def analyze(self) -> bool:
        """Analyze how to (and if possible to) download gif"""
        raise NotImplementedError

    # def download(self) -> list:
    #     return self.files


class GifHost:
    name = None
    regex = None
    url_template = None
    priority = 0
    ghm = None
    gif_type = Gif
    # Can upload gif
    can_gif = True
    # Can upload vid
    can_vid = True
    # Can upload audio
    audio = False
    # Preferred video type
    video_type = consts.MP4
    # Video length limit in secs
    vid_len_limit = 0
    # Video size limit in MB
    vid_size_limit = 0
    # Gif size limit in MB
    gif_size_limit = 0
    # Gif frame count limit
    gif_frame_limit = 0

    @classmethod
    def upload(cls, file, gif_type, nsfw):
        raise NotImplementedError

    @classmethod
    def get_gif(cls, id=None, regex=None, url=None, context=None) -> Gif:
        if url:
            regex = cls.regex.findall(url)
        if regex:
            gif_id = regex[0]
        if gif_id:
            return cls.gif_type(cls, gif_id, context=context)

    @classmethod
    def match(cls, text):
        return len(cls.regex.findall(text)) != 0


def get_response_size(url, max=None):
    """Returns size in MB"""
    if max:
        max_bytes = max * 1000000
    size = 0
    with requests.get(url, stream=True) as r:
        for chunk in r.iter_content(8196):
            size += len(chunk)
            if max:
                if size > max_bytes:
                    return False
    return size / 1000000

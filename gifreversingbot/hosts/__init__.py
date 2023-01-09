import os
import requests
from io import BytesIO
from gifreversingbot.core import constants as consts
from gifreversingbot.core.file import get_frames, get_duration, has_audio, MediaInfo, estimate_frames_to_pngs

NO_NSFW = 1
NSFW_ALLOWED = 2
ONLY_NSFW = 3


# Message constants
# If a host is unable/unwilling to accept a specific gif
class CannotUpload:
    pass


# If a host had a temporary failure/problem that inhibited the upload
class UploadFailed:
    pass


class GifFile:
    def __init__(self, file, host=None, gif_type=None, size=None, duration=None, frames=0, audio=None, conversion=None):
        self.file = file
        self.info = MediaInfo(self.file)
        self.file.seek(0)
        self.type = gif_type
        self.size = None
        self.frames = frames
        # Make unified metadata grabber function

        if audio is None:
            self.audio = False
        else:
            if audio:
                self.audio = True
            else:
                self.audio = has_audio(self.file)
        if gif_type == consts.GIF and not frames:
            self.frames = get_frames(self.file)
            if self.frames == 0:
                if self.info.frame_count:
                    self.frames = self.info.frame_count
        if size:
            self.size = size
        else:
            if isinstance(file, BytesIO):
                self.size = file.getbuffer().nbytes / 1000000
            else:
                self.size = os.fstat(file.fileno()).st_size / 1000000  # Convert to MB

        if duration:
            self.duration = duration
        else:
            self.duration = get_duration(self.file)

        self.conversion = conversion
        if self.conversion:
            # If we are converting from MP4 to GIF we to need to estimate the resulting size
            if conversion == consts.MP4 and self.type == consts.GIF:
                self.pngs_size = estimate_frames_to_pngs(self.info.dimensions[0], self.info.dimensions[1], self.frames)

        self.host = host

    def __del__(self):
        self.file.close()


class Gif:
    process_id = False

    def __init__(self, host, id, context=None, url=None, nsfw=False):
        self.host = host
        self.context = context
        if self.context:
            self.nsfw = self.context.nsfw or nsfw
            if not url:
                url = self.context.url
        else:
            self.nsfw = nsfw

        self.pic = None
        self.file = None
        self.size = None
        self.type = None
        self.duration = None
        self.files = []

        if not self.process_id or not url:  # URL is required to do ID processing. If we are
            self.id = id                         # missing
        else:
            self.id = self._get_id(id, url)
        self.url = self.host.url_template.format(self.id)

    def __repr__(self):
        return "{}-{}".format(self.host.name, self.id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return False

    def _get_id(self, id, url):
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
    # Allows NSFW
    NSFW = NSFW_ALLOWED
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
    def upload(cls, file, gif_type, nsfw, audio=False):
        raise NotImplementedError

    @classmethod
    def delete(cls, gif):
        raise NotImplementedError

    @classmethod
    def get_gif(cls, id=None, regex=None, text=None, **kwargs) -> Gif:
        url = None
        if text:
            regex = cls.regex.findall(text)
        if regex:
            id = regex[0]
            url = cls.regex.search(text).group()
        if id:
            return cls.gif_type(cls, id, url=url, **kwargs)

    @classmethod
    def match(cls, text):
        return len(cls.regex.findall(text)) != 0

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def get_response_size(url, max=None):
    """Returns size in MB"""
    if max:
        max_bytes = max * 1000000
    size = 0
    headers = {"User-Agent": consts.spoof_user_agent}
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            for chunk in r.iter_content(8196):
                size += len(chunk)
                if max:
                    if size > max_bytes:
                        return False
        return size / 1000000
    except Exception as e:
        print(e, dir(e))
        raise e
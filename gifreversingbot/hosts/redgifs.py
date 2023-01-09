from gifreversingbot.hosts.gfycat import GfycatHost, GfycatGif, GfycatClient
from gifreversingbot.hosts import ONLY_NSFW
import gifreversingbot.core.constants as consts


class RedgifsClient(GfycatClient):
    pass


class RedgifsGif(GfycatGif):
    pass


class RedgifsHost(GfycatHost):
    name = "Redgifs"
    url_template = "https://redgifs.com/{}"
    gif_type = RedgifsGif
    NSFW = ONLY_NSFW
    video_type = consts.WEBM
    vid_len_limit = 61  # This has been double verified now lol
    gif_size_limit = 1700   # Gfycat doesn't have a real limit but I doubt anything higher than this will work
    gif_frame_limit = 2100
    API = RedgifsClient.get()

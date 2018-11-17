import requests
from io import BytesIO
from imgurpython.imgur.models.gallery_image import GalleryImage
from imgurpython.helpers.error import ImgurClientError

import core.hosts.imgur
from core import constants as consts
from core.gif import Gif
from core.regex import REPatterns
from core.hosts.imgur import ImgurClient
from core.hosts.gfycat import Gfycat as GfycatClient
from core.hosts.streamable import StreamableClient
from core.credentials import CredentialsLoader
from core.file import get_duration


creds = CredentialsLoader.get_credentials()
imgur = ImgurClient.get()
gfycat = GfycatClient.get()
streamable = StreamableClient.get()


class GifHost:
    type = None

    def __init__(self, context):
        self.context = context

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
            return Gif(self.type, self.id, nsfw=self.context.nsfw)
        else:
            return None

    @classmethod
    def open(cls, context, reddit):
        url = context.url
        # Imgur
        if REPatterns.imgur.findall(url):
            return ImgurGif(context)
        # Gfycat
        if REPatterns.gfycat.findall(url):
            return GfycatGif(context)
        # Reddit Gif
        if REPatterns.reddit_gif.findall(url):
            return RedditGif(context)
        # Reddit Vid
        if REPatterns.reddit_vid.findall(url):
            return RedditVid(context, reddit)
        # Streamable
        if REPatterns.streamable.findall(url):
            return Streamable(context)

        print("Unknown URL Type", url)
        return None


class ImgurGif(GifHost):
    type = consts.IMGUR

    def __init__(self, context):
        super(ImgurGif, self).__init__(context)
        self.uploader = consts.IMGUR

        # Retrieve the ID
        imgur_match = REPatterns.imgur.findall(self.context.url)[0]

        # Try block for catching imgur 404s
        try:
            if imgur_match[4]: # Image match
                self.id = imgur_match[4]
            elif imgur_match[3]: # Gallery match
                gallery = imgur.gallery_item(imgur_match[3])
                if not isinstance(gallery, GalleryImage):
                    self.id = gallery.images[0]['id']   # First image from gallery album
                else:
                    self.id = gallery.id
            elif imgur_match[2]: # Album match
                album = imgur.get_album(imgur_match[2])
                self.id = album.images[0]['id'] # First image of album

            self.pic = imgur.get_image(self.id)  # take first image from gallery album

        except ImgurClientError as e:
            print("Imgur returned 404, deleted image?")
            if e.status_code == 404:
                self.pic = None
                self.id = None

    def analyze(self):
        """Analyze an imgur gif using the imgurpython library and determine how to reverse and upload"""

        # pprint(vars(self.pic))

        if not self.pic.animated:
            print("Not a gif!")
            return False
        r = requests.get(self.pic.mp4)
        duration = get_duration(BytesIO(r.content))

        # If under a certain duration, it was likely uploaded as an mp4 (and it's easier
        # for us to reverse it that way anyways)
        if duration < 31:  # Interestingly, imgur appears to allow mp4s under 31 seconds
            self.url = self.pic.mp4  # (rather than capping at 30 like they advertise)
            return consts.VIDEO
        else:               # has to have been a gif
            self.url = self.pic.gifv[:-1]
            size = get_gif_size(self.url)
            print("size in MB", size)
            # Due to gifski bloat, we may need to redirect to gfycat
            if size > 175:
                self.uploader = consts.GFYCAT
            return consts.GIF

    def upload_video(self, video):
        return core.hosts.imgur.imgurupload(video, consts.VIDEO, nsfw=self.context.nsfw)


    def upload_gif(self, gif):
        if self.uploader == consts.IMGUR:
            return core.hosts.imgur.imgurupload(gif, consts.GIF, nsfw=self.context.nsfw)
        elif self.uploader == consts.GFYCAT:
            return gfycat.upload(gif, consts.GIF, nsfw=self.context.nsfw)

class GfycatGif(GifHost):
    type = consts.GFYCAT

    def __init__(self, context):
        super(GfycatGif, self).__init__(context)
        self.id = REPatterns.gfycat.findall(context.url)[0]
        self.pic = gfycat.get_gfycat(self.id)
        self.url = self.pic["gfyItem"]["mp4Url"]

    def analyze(self):
        return consts.VIDEO

    def upload_video(self, video):
        return gfycat.upload(video, consts.VIDEO, nsfw=self.context.nsfw)

class RedditGif(GifHost):
    type = consts.REDDITGIF

    def __init__(self, context):
        super(RedditGif, self).__init__(context)
        self.id = REPatterns.reddit_gif.findall(context.url)[0]
        self.url = context.url

    def analyze(self):
        return consts.GIF

    def upload_gif(self, gif):
        return core.hosts.imgur.imgurupload(gif, consts.GIF)

class RedditVid(GifHost):
    type = consts.REDDITVIDEO

    def __init__(self, context, reddit):
        super(RedditVid, self).__init__(context)
        self.uploader = consts.IMGUR
        self.id = REPatterns.reddit_vid.findall(self.context.url)[0]
        headers = {"User-Agent": consts.spoof_user_agent}
        # Follow redirect to post URL
        r = requests.get(self.context.url, headers=headers)
        submission_id = REPatterns.reddit_submission.findall(r.url)
        if submission_id:
            submission = reddit.submission(id=REPatterns.reddit_submission.findall(r.url)[0][1])
            if submission.is_video:
                self.url = submission.media['reddit_video']['fallback_url']
                print(self.url)
        else:   # Maybe it was deleted?
            self.id = None

    def analyze(self):
        r = requests.get(self.url)
        duration = get_duration(BytesIO(r.content))
        if duration <= 30:  # likely uploaded as a mp4, reupload through imgur
            self.uploader = consts.IMGUR
            return consts.VIDEO
        elif duration <= 60: # fallback to gfycat
            self.uploader = consts.GFYCAT
            return consts.VIDEO
        else:  # fallback as a gif, upload to gfycat
            # I would like to be able to predict a >200MB GIF file size and switch from
            # Imgur to Gfycat as a result
            if self.context.nsfw:
                self.uploader = consts.GFYCAT
                return consts.GIF
            else:
                self.uploader = consts.STREAMABLE
                return consts.VIDEO

    def upload_video(self, video):
        if self.uploader == consts.IMGUR:
            return core.hosts.imgur.imgurupload(video, consts.VIDEO, nsfw=self.context.nsfw)
        elif self.uploader == consts.GFYCAT:
            return gfycat.upload(video, consts.VIDEO, nsfw=self.context.nsfw)
        elif self.uploader == consts.STREAMABLE:
            return streamable.upload_file(video, 'GifReversingBot - {}'.format(self.get_gif().url))

    def upload_gif(self, gif):
        if self.uploader == consts.IMGUR:
            return core.hosts.imgur.imgurupload(gif, consts.GIF, nsfw=self.context.nsfw)
        elif self.uploader == consts.GFYCAT:
            return gfycat.upload(gif, consts.GIF, nsfw=self.context.nsfw)


class Streamable(GifHost):
    type = consts.STREAMABLE

    def __init__(self, context):
        super(Streamable, self).__init__(context)
        self.id = REPatterns.streamable.findall(self.context.url)[0]

    @property
    def url(self):
        return streamable.download_video(self.id)

    def analyze(self):
        return consts.VIDEO

    def upload_video(self, video):
        return streamable.upload_file(video, 'GifReversingBot - {}'.format(self.get_gif().url))



class LinkGif(GifHost):
    pass

def get_gif_size(url):
    """Returns size in MB"""
    with requests.get(url, stream=True) as r:
        size = sum(len(chunk) for chunk in r.iter_content(8196))
    return size / 1000000
import requests
from io import BytesIO

from core import constants as consts
from core.hosts import GifHost, Gif, GifFile
from core.regex import REPatterns
from core.file import get_duration, get_fps


class RedditVid(Gif):
    def analyze(self) -> bool:
        headers = {"User-Agent": consts.spoof_user_agent}
        r = requests.get("https://v.redd.it/{}".format(self.id), headers=headers)
        submission_id = REPatterns.reddit_submission.findall(r.url)
        url = None
        if submission_id:
            submission = self.host.ghm.reddit.submission(id=submission_id[0][2])
            if submission.is_video:
                url = submission.media['reddit_video']['fallback_url']
        else:  # Maybe it was deleted?
            print("Deleted?")
            return False
        r = requests.get(url)
        file = BytesIO(r.content)
        self.type = consts.MP4
        self.duration = get_duration(file)
        self.size = file.getbuffer().nbytes / 1000000
        self.files.append(GifFile(file, self.host, self.type, self.size, self.duration))
        self.files.append(GifFile(file, self.host, consts.GIF, self.size, self.duration))
        return True


class RedditVideoHost(GifHost):
    name = "RedditVideo"
    regex = REPatterns.reddit_vid
    url_template = "https://v.redd.it/{}"
    gif_type = RedditVid
    can_gif = False
    can_vid = False

    @classmethod
    def get_gif(cls, id=None, regex=None, url=None, context=None) -> Gif:
        # Parse submission urls
        if REPatterns.reddit_submission.findall(url):
            reddit = cls.ghm.reddit
            submission = reddit.submission(REPatterns.reddit_submission.findall(context.url)[0][2])
            if submission.media:
                if submission.media.get('reddit_video', False):
                    # Not a reddit gif
                    return cls.ghm.extract_gif(submission.media['reddit_video']['fallback_url'], context=context)
            url = submission.url
        if url:
            regex = cls.regex.findall(url)
        if regex:
            gif_id = regex[0]
        if gif_id:
            return cls.gif_type(cls, gif_id, context=context)

    @classmethod
    def match(cls, text):
        return len(cls.regex.findall(text)) != 0 or len(REPatterns.reddit_submission.findall(text)) != 0

class RedditGif(Gif):
    def analyze(self) -> bool:
        self.type = consts.GIF
        self.file = BytesIO(requests.get(self.url).content)
        self.size = self.file.getbuffer().nbytes / 1000000
        self.files.append(GifFile(self.file, self.host, self.type, self.size))
        return True

class RedditGifHost(GifHost):
    name = "RedditGif"
    regex = REPatterns.reddit_gif
    url_template = "https://i.redd.it/{}.gif"
    gif_type = RedditGif
    can_gif = False
    can_vid = False

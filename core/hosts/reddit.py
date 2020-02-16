import requests
from io import BytesIO
from prawcore.exceptions import ResponseException

from core import constants as consts
from core.hosts import GifHost, Gif, GifFile
from core.regex import REPatterns
from core.file import get_duration, get_fps
from core.concat import concat


class RedditVid(Gif):
    def analyze(self) -> bool:
        headers = {"User-Agent": consts.spoof_user_agent}
        r = requests.get("https://v.redd.it/{}".format(self.id), headers=headers)
        submission_id = REPatterns.reddit_submission.findall(r.url)
        url = None
        audio = False
        if not submission_id:
            print("Deleted?")
            return False
        elif submission_id[0][2]:
            submission = self.host.ghm.reddit.submission(id=submission_id[0][2])
            try:
                if submission.is_video:
                    if submission.media:
                        url = submission.media['reddit_video']['fallback_url']
                    else:
                        print("Submission is video but there is no media data")
                        return False
            except ResponseException as e:
                print("Video is inaccessible, likely deleted")
                return False

        else:  # Maybe it was deleted?
            print("Deleted?")
            return False


        r = requests.get(url)
        file = BytesIO(r.content)

        r = requests.get("https://v.redd.it/{}/audio".format(self.id), headers=headers)
        if r.status_code == 200:
            file = concat(file, BytesIO(r.content))
            audio = True

        self.type = consts.MP4
        self.size = file.getbuffer().nbytes / 1000000
        self.files.append(GifFile(file, self.host, self.type, self.size, audio=audio))
        self.files.append(GifFile(file, self.host, consts.GIF, self.size))
        return True


class RedditVideoHost(GifHost):
    name = "RedditVideo"
    regex = REPatterns.reddit_vid
    url_template = "https://v.redd.it/{}"
    gif_type = RedditVid
    can_gif = False
    can_vid = False

    @classmethod
    def get_gif(cls, id=None, regex=None, text=None, **kwargs) -> Gif:
        url = None
        if text:
            # Parse submission urls
            subregex = REPatterns.reddit_submission.findall(text)
            if subregex:
                if subregex[0][2]:
                    reddit = cls.ghm.reddit
                    submission = reddit.submission(subregex[0][2])
                    regex = cls.regex.findall(submission.url)
                    if regex:
                        # Modify text to be a v.redd.it link for down the line parsing
                        text = submission.url
                    else:
                        # Not a reddit vid
                        if submission.is_self:      # Selfposts just link to themselves, are not a redirect
                            return None
                        return cls.ghm.extract_gif(submission.url, **kwargs)
            regex = cls.regex.findall(text)
        if regex:
            id = regex[0]
            # For whatever terrible reason, fullmatch doesn't work with this regex statement. No idea why. God help me
            # url = cls.regex.fullmatch(text).string
        if id:
            return cls.gif_type(cls, id, url=url, **kwargs)

    @classmethod
    def match(cls, text):
        # print(cls.regex.findall(text), REPatterns.reddit_submission.findall(text))
        sub = REPatterns.reddit_submission.findall(text)
        if sub:
            if sub[0][2]:
                return True
        return len(cls.regex.findall(text)) != 0

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

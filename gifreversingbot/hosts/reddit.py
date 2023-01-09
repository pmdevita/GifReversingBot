import requests
import re
from io import BytesIO
from prawcore.exceptions import ResponseException

from gifreversingbot.core import constants as consts
from gifreversingbot.hosts import GifFile, Gif, GifHost
from gifreversingbot.core.concat import concat

REDDIT_SUBMISSION = re.compile("http(?:s)?://(?:\w+?\.)?reddit.com(/r/|/user/)?(?(1)(\w{2,21}))(/comments/)?(?(3)(\w{5,7})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?")


class RedditVid(Gif):
    def analyze(self) -> bool:
        headers = {"User-Agent": consts.spoof_user_agent}
        r = requests.get("https://v.redd.it/{}".format(self.id), headers=headers)
        submission_regex = REDDIT_SUBMISSION.findall(r.url)
        url = None
        audio = False

        if not submission_regex:
            print("Deleted?")
            return False

        submission_id = submission_regex[0][3]
        submission = self.host.ghm.reddit.submission(submission_id)
        try:
            if not submission.is_video:
                print("Reddit submission is not marked as a video.")
                return False
            if not submission.media:
                print("Submission is video but there is no media data")
                return False
            if submission.media['reddit_video'].get('fallback_url', None):
                url = submission.media['reddit_video']['fallback_url']
            elif submission.media['reddit_video'].get("transcoding_status", None) == "error":
                print("Reddit had an error transcoding this video")
                return False
        except ResponseException as e:
            print("Video is inaccessible, likely deleted")
            return False

        r = requests.get(url)
        if r.status_code != 200:
            print("Getting Reddit Video returned status, deleted?", r.status_code)
            return False
        file = BytesIO(r.content)

        r = requests.get("https://v.redd.it/{}/DASH_audio.mp4".format(self.id), headers=headers)
        if r.status_code == 200:
            file = concat(file, BytesIO(r.content))
            audio = True

        if not audio:
            # Audio could be here instead
            r = requests.get("https://v.redd.it/{}/audio".format(self.id), headers=headers)
            if r.status_code == 200:
                file = concat(file, BytesIO(r.content))
                audio = True

        self.type = consts.MP4
        self.size = file.getbuffer().nbytes / 1000000
        self.files.append(GifFile(file, self.host, self.type, self.size, audio=audio))
        # self.files.append(GifFile(file, self.host, consts.GIF, self.size))
        return True


class RedditVideoHost(GifHost):
    name = "RedditVideo"
    regex = re.compile("https?://v.redd.it/(\w+)")
    url_template = "https://v.redd.it/{}"
    gif_type = RedditVid
    can_gif = False
    can_vid = False

    @classmethod
    def get_gif(cls, id=None, regex=None, text=None, **kwargs) -> Gif:
        url = None
        if text:
            # Parse submission urls
            subregex = REDDIT_SUBMISSION.findall(text)
            if subregex:
                if subregex[0][3]:
                    reddit = cls.ghm.reddit
                    try:
                        submission = reddit.submission(subregex[0][3])
                        regex = cls.regex.findall(submission.url)
                    except ResponseException:
                        print("Submission does not exist")
                        return None
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
        sub = REDDIT_SUBMISSION.findall(text)
        if sub:
            if sub[0][3]:
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
    regex = re.compile("http(?:s)?://i.redd.it/(.*?)\.gif")
    url_template = "https://i.redd.it/{}.gif"
    gif_type = RedditGif
    can_gif = False
    can_vid = False

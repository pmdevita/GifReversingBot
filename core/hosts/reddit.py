from core.hosts import GifHost
from core.regex import REPatterns
from core.gif import Gif


class RedditVideoHost(GifHost):
    name = "RedditVideo"
    regex = REPatterns.reddit_vid
    url = "https://v.redd.it/{}"


class RedditGifHost(GifHost):
    name = "RedditGif"
    regex = REPatterns.reddit_gif
    url = "https://i.redd.it/{}.gif"

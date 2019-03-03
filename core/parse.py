import validators
import re
from core.regex import REPatterns

def old_validate_url(url):
    """Validate a URL by checking it against Validators and our regex"""
    if validators.url(url):
        return url_host(url)


def extract_url(text):
    # Imgur
    if REPatterns.imgur.findall(text):
        return REPatterns.imgur.findall(text)
    # Gfycat
    if REPatterns.gfycat.findall(text):
        return REPatterns.gfycat.findall(text)
    # Reddit Gif
    if REPatterns.reddit_gif.findall(text):
        return REPatterns.reddit_gif.findall(text)
    # Reddit Vid
    if REPatterns.reddit_vid.findall(text):
        return REPatterns.reddit_vid.findall(text)
    # Streamable
    if REPatterns.streamable.findall(text):
        return REPatterns.streamable.findall(text)
    # Reddit Submission
    if REPatterns.reddit_submission.findall(text):
        return REPatterns.reddit_submission.findall(text)
    if REPatterns.link_gif.findall(text):
        return REPatterns.reddit_submission.findall(text)

    # print("Unknown URL Type", text)
    return False


def url_host(url):
    # Imgur
    if REPatterns.imgur.findall(url):
        return True
    # Gfycat
    if REPatterns.gfycat.findall(url):
        return True
    # Reddit Gif
    if REPatterns.reddit_gif.findall(url):
        return True
    # Reddit Vid
    if REPatterns.reddit_vid.findall(url):
        return True
    # Streamable
    if REPatterns.streamable.findall(url):
        return True
    # Reddit Submission
    if REPatterns.reddit_submission.findall(url)[0][2]:
        return True
    # Link to GIF
    if REPatterns.link_gif.findall(url):
        return True

    print("Unknown URL Type", url)
    return False

import validators
import re
from core.regex import REPatterns


def get_url(comment):
    """Retrieve a URL from a comment"""
    tokens = comment.body.split()

    if len(tokens) >= 2:  # first check for direct request
        for i in tokens:
            if validate_url(i):
                return i
    if comment.is_root:
        if validate_url(comment.submission.url):
            return comment.submission.url
    else:
        for i in getcommentparent(comment).body.split():
            if validate_url(i):
                return i

    return None


def validate_url(url):
    """Validate a URL by checking it against Validators and our regex"""
    return validators.url(url) and not REPatterns.textpost.match(url)

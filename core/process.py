import requests
from io import BytesIO

from core.context import CommentContext
from core.reply import reply
from core.gif_host import GifHost
from core.reverse import reverse_mp4, reverse_gif
from core.concat import concat, vid_to_gif
from core.history import check_database, add_to_database
from core import constants as consts


def process_comment(reddit, comment):
    # Check if comment is deleted
    if not comment.author:
        print("Comment doesn't exist????")
        print(vars(comment))
        return

    print("New request by " + comment.author.name)

    # Create the comment context object
    context = CommentContext(reddit, comment)
    if not context.url:         # Did our search return nothing?
        print("Didn't find a URL")
        return

    if context.rereverse:           # Is the user asking to rereverse?
        reply(context, context.url)
        return

    # Create object to grab gif from host
    print(context.url)
    gif_host = GifHost.open(context, reddit)

    # If the link was not recognized, return
    if not gif_host:
        return

    # If the gif was unable to be acquired, return
    original_gif = gif_host.get_gif()
    if not original_gif:
        return

    # Check database for gif before we reverse it
    gif = check_database(original_gif)

    # If it was in the database, reuse it
    if gif:
        reply(context, gif.url)
        return

    # Analyze how the gif should be reversed
    method = gif_host.analyze()

    # If there was some problem analyzing, exit
    if not method:
        return

    reversed_gif = None

    r = requests.get(gif_host.url)

    # Reverse it as a GIF
    if method == consts.GIF:
        # With reversed gif
        with vid_to_gif(BytesIO(r.content)) as f:
            # Give to gif_host's uploader
            reversed_gif = gif_host.upload_gif(f)
    # Reverse it as a video
    elif method == consts.VIDEO:
        if gif_host.audio:
            audio = requests.get(gif_host.audio)
            with concat(BytesIO(r.content), BytesIO(audio.content)) as f:
                reversed_gif = gif_host.upload_video(f)
        else:
            reversed_gif = gif_host.upload_video(BytesIO(r.content))
    # Defer to the object's unique method
    elif method == consts.OTHER:
        reversed_gif = gif_host.reverse()
    elif method == consts.LINK:
        reversed_gif = gif_host.upload_link(gif_host.url)

    if reversed_gif:
        # Add gif to database
        if reversed_gif.log:
            add_to_database(gif_host.get_gif(), reversed_gif)
        # Reply
        print("Replying!", reversed_gif.url)
        reply(context, reversed_gif.url)
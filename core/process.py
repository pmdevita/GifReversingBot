import requests
from io import BytesIO

from core.context import CommentContext
from core.reply import reply
from core.gif_host import GifHost
from core.reverse import reverse_mp4, reverse_gif
from core.history import check_database, add_to_database, delete_from_database
from core import constants as consts
from core.constants import SUCCESS, USER_FAILURE, UPLOAD_FAILURE


def process_comment(reddit, comment=None, queue=None, original_context=None):
    if not original_context:    # If we were not provided context, make our own
        # Check if comment is deleted
        if not comment.author:
            print("Comment doesn't exist????")
            print(vars(comment))
            return USER_FAILURE

        print("New request by " + comment.author.name)

        # Create the comment context object
        context = CommentContext(reddit, comment)
        if not context.url:         # Did our search return nothing?
            print("Didn't find a URL")
            return USER_FAILURE

        if context.rereverse and not context.reupload:  # Is the user asking to rereverse?
            reply(context, context.url)
            return SUCCESS

    else:   # If we are the client, context is provided to us
        context = original_context

    # Create object to grab gif from host
    print(context.url)
    gif_host = GifHost.open(context, reddit)

    # If the link was not recognized, return
    if not gif_host:
        return USER_FAILURE

    # If the gif was unable to be acquired, return
    original_gif = gif_host.get_gif()
    if not original_gif:
        return USER_FAILURE

    if queue:
        # Add to queue
        print("Adding to queue...")
        queue.add_job(context.to_json(), original_gif)
        return SUCCESS

    # Check database for gif before we reverse it
    gif = check_database(original_gif)

    if gif:
        # If we were asked to reupload, double check the gif
        if context.reupload:
            print("Doing a reupload check...")
            if not is_reupload_needed(gif, reddit):
                # No reupload needed, do normal stuff
                reply(context, gif)
                print("No reupload needed")
                return SUCCESS
            else:
                # Reupload is needed, delete this from the database
                delete_from_database(gif)
                print("Reuploadng needed")
        # Proceed as normal
        else:
            # If it was in the database, reuse it
            reply(context, gif)
            return SUCCESS

    # Analyze how the gif should be reversed
    in_format, out_format = gif_host.analyze()

    # If there was some problem analyzing, exit
    if not in_format or not out_format:
        return USER_FAILURE

    reversed_gif = None

    if isinstance(gif_host.url, str):
        r = requests.get(gif_host.url)
    elif isinstance(gif_host.url, requests.Response):
        r = gif_host.url

    # If we 404, it must not exist
    if r.status_code == 404:
        print("Gif not found at URL")
        return USER_FAILURE

    # Reverse it as a GIF
    if out_format == consts.GIF:
        # With reversed gif
        with reverse_gif(BytesIO(r.content), format=in_format) as f:
            # Give to gif_host's uploader
            reversed_gif = gif_host.upload_gif(f)
    # Reverse it as a video
    elif out_format == consts.MP4:
        with reverse_mp4(BytesIO(r.content), original_gif.audio, format=in_format) as f:
            reversed_gif = gif_host.upload_video(f)
    elif out_format == consts.WEBM:
        with reverse_mp4(BytesIO(r.content), original_gif.audio, format=in_format, output=consts.WEBM) as f:
            reversed_gif = gif_host.upload_video(f)
    # Defer to the object's unique method
    elif out_format == consts.OTHER:
        reversed_gif = gif_host.reverse()

    if reversed_gif:
        # Add gif to database
        if reversed_gif.log:
            add_to_database(gif_host.get_gif(), reversed_gif)
        # Reply
        print("Replying!", reversed_gif.url)
        reply(context, reversed_gif)
        return SUCCESS
    else:
        return UPLOAD_FAILURE


def process_mod_invite(reddit, message):
    subreddit_name = message.subject[26:]
    # Sanity
    if len(subreddit_name) > 2:
        subreddit = reddit.subreddit(subreddit_name)
        subreddit.mod.accept_invite()
        print("Accepted moderatership at", subreddit_name)
        return subreddit_name

def is_reupload_needed(gif, reddit):
    in_format, out_format = None, None
    # The gif should return None if missing
    original_gif_host = GifHost.from_gif(gif, reddit)
    # If host grabbing was successful
    if original_gif_host:
        original_gif = original_gif_host.get_gif()
        # If gif grabbing was successful
        if original_gif:
            in_format, out_format = gif_host.analyze()
            # If analysis was successful
            if in_format and out_format:
                # No need to reupload
                return False
    # We need to reupload
    return True

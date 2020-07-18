from io import BytesIO
import praw.exceptions
from core.context import CommentContext
from core.reply import reply
from core.gif import GifHostManager, CANNOT_UPLOAD, UPLOAD_FAILED
from core.reverse import reverse_mp4, reverse_gif
from core.history import check_database, add_to_database, delete_from_database
from core import constants as consts
from core.hosts import GifFile, Gif
from core.constants import SUCCESS, USER_FAILURE, UPLOAD_FAILURE


def process_comment(reddit, comment=None, queue=None, original_context=None):
    ghm = GifHostManager(reddit)
    if not original_context:  # If we were not provided context, make our own
        # Check if comment is deleted
        try:
            if not comment.author:
                print("Comment doesn't exist????")
                print(vars(comment))
                return USER_FAILURE
        except praw.exceptions.PRAWException as e:
            print(e)
            return USER_FAILURE

        print("New request by " + comment.author.name)

        # Create the comment context object
        context = CommentContext(reddit, comment, ghm)
        if not context.url:  # Did our search return nothing?
            print("Didn't find a URL")
            return USER_FAILURE

        if context.rereverse and not context.reupload:  # Is the user asking to rereverse?
            reply(context, context.url)
            return SUCCESS

    else:  # If we are the client, context is provided to us
        context = original_context

    # Create object to grab gif from host
    # print(context.url)
    # gif_host = GifHost.open(context, reddit)

    # new_original_gif = ghm.extract_gif(context.url, context=context)
    new_original_gif = context.url
    print(new_original_gif)

    # If the link was not recognized, return
    # if not gif_host:
    #     return USER_FAILURE

    if not new_original_gif:
        return USER_FAILURE

    # If the gif was unable to be acquired, return
    # original_gif = gif_host.get_gif()
    # if not original_gif:
    #     return USER_FAILURE

    if not new_original_gif.id:
        return USER_FAILURE

    if queue:
        # Add to queue
        print("Adding to queue...")
        queue.add_job(context.to_json(), new_original_gif)
        return SUCCESS

    # Check database for gif before we reverse it
    gif = check_database(new_original_gif)

    # Requires new database setup
    # db_gif = check_database(new_original_gif)

    if gif:  # db_gif
        # If we were asked to reupload, double check the gif
        if context.reupload:
            print("Doing a reupload check...")
            if not is_reupload_needed(reddit, gif):
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
    # in_format, out_format = gif_host.analyze()

    # If there was some problem analyzing, exit
    # if not in_format or not out_format:
    #     return USER_FAILURE

    if not new_original_gif.analyze():
        return USER_FAILURE

    uploaded_gif = None

    # This gif cannot be uploaded and it is not our fault
    cant_upload = False

    # Try every option we have for reversing a gif
    options = ghm.get_upload_host(new_original_gif)

    if not options:
        print("File too large {}s {}MB".format(new_original_gif.files[0].duration, new_original_gif.files[0].size))
        cant_upload = True
    else:
        cant_upload = False

    for option in options:
        upload_gif_host = option['hosts'][0]
        original_gif_file = option['file']

        # Temporarily halt any uploads to Redgifs
        if upload_gif_host == ghm['Redgifs']:
            print("Blocked Redgifs upload")
            cant_upload = False
            break

        r = original_gif_file.file

        # Reverse it as a GIF
        if original_gif_file.type == consts.GIF:
            # With reversed gif
            f = reverse_gif(r, format=original_gif_file.type)
            # Give to gif_host's uploader
            reversed_gif_file = GifFile(f, original_gif_file.host, consts.GIF,
                                        duration=original_gif_file.duration, frames=original_gif_file.frames)
            # reversed_gif = upload_gif_host.upload(f, consts.GIF, new_original_gif.context.nsfw)
        # Reverse it as a video
        else:
            f = reverse_mp4(r, original_gif_file.audio, format=original_gif_file.type,
                            output=upload_gif_host.video_type)
            reversed_gif_file = GifFile(f, original_gif_file.host, upload_gif_host.video_type,
                                        duration=original_gif_file.duration, audio=original_gif_file.audio)
            # reversed_gif = upload_gif_host.upload(f, upload_gif_host.video_type, new_original_gif.context.nsfw)

        # Attempt a first upload
        options = ghm.get_upload_host(new_original_gif, file=reversed_gif_file)
        # If there was no suitable upload host, this format cannot be uploaded
        if not options:
            cant_upload = True
            continue

        # Using the provided host, perform the upload
        for i in range(2):
            result = options[0]['hosts'][0].upload(reversed_gif_file.file, reversed_gif_file.type,
                                                   new_original_gif.nsfw, reversed_gif_file.audio)
            # If the host simply cannot accept this file at all
            if result == CANNOT_UPLOAD:
                cant_upload = True
                break
            # If the host was unable to accept the gif at this time
            elif result == UPLOAD_FAILED:
                cant_upload = False
                continue  # Try again?
            # No error and not None, success!
            elif result:
                uploaded_gif = result
                break

        # If we have the uploaded gif, break out and continue
        if uploaded_gif:
            break

    # If there was an error, return it
    if cant_upload:
        return USER_FAILURE
    # It's not that it was an impossible request, there was something else
    elif not uploaded_gif:
        return UPLOAD_FAILURE

    if uploaded_gif:
        # Add gif to database
        # if reversed_gif.log:
        add_to_database(new_original_gif, uploaded_gif)
        # Reply
        print("Replying!", uploaded_gif.url)
        reply(context, uploaded_gif)
        return SUCCESS
    else:
        return UPLOAD_FAILURE


def process_mod_invite(reddit, message):
    subreddit_name = message.subject[26:]
    # Sanity
    if len(subreddit_name) > 2:
        subreddit = reddit.subreddit(subreddit_name)
        try:
            subreddit.mod.accept_invite()
            print("Accepted moderatership at", subreddit_name)
            return subreddit_name
        except praw.exceptions.APIException as e:
            if e.error_type == "NO_INVITE_FOUND":
                print("Got an invite from {} which was immediately revoked".format(subreddit_name))


def is_reupload_needed(reddit, gif: Gif):
    if gif.id:
        if gif.analyze():
            return False
    return True

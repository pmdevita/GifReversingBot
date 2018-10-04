import praw.exceptions
import prawcore.exceptions
from core import constants as consts

def reply(comment, context):
    url = context.url
    try:
        if not context.nsfw:
            comment.reply(consts.reply_template.format(url))
        else:
            comment.reply(consts.nsfw_reply_template.format(url))
    except praw.exceptions.APIException as err:
        error = vars(err)
        if err.error_type == "RATELIMIT":
            errtokens = error['message'].split()
            print("Oops! Hit the rate limit! Gotta wait " + errtokens[len(errtokens) - 2] + " " + errtokens[
                len(errtokens) - 1])
    except prawcore.exceptions.Forbidden as err:
        # Probably banned, message the gif to them
        comment.author.message(consts.ban_message_subject, consts.ban_message_template.format(url))
    print("Successfully reversed and replied!")
import praw
import prawcore
import time
import traceback
from core.process import process_comment
from core.credentials import CredentialsLoader
from core.regex import REPatterns
from core import constants as consts
from core.secret import secret_process

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

print("GifReversingBot v{} Ctrl+C to stop".format(consts.version))

while True:
    try:
        for message in reddit.inbox.unread():
            if message.was_comment:
                if message.subject == "username mention":
                    process_comment(reddit, reddit.comment(message.id))
                elif message.subject == "comment reply" or message.subject == "post reply":
                    if REPatterns.reply_mention.findall(message.body):
                        process_comment(reddit, reddit.comment(message.id))
                    else:
                        secret_process(reddit, message)
            else:  # was a message
                # if message.first_message == "None":
                #     message.reply("Sorry, I'm only a bot! I'll contact my creator /u/pmdevita for you.")
                reddit.redditor(operator).message("Someone messaged me!",
                                                    "Subject: " + message.subject + "\n\nContent:\n\n" + message.body)

            reddit.inbox.mark_read([message])

        time.sleep(consts.sleep_time)

    except prawcore.exceptions.ResponseException as e:   # Something funky happened
        print("Did a comment go missing?", e, vars(e))
        time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        print("Exiting...")
        break

    except Exception as e:
        if mode == "production":
            reddit.redditor(operator).message("GRB Error!", "Help I crashed!\n\n    {}".format(
                str(traceback.format_exc()).replace('\n', '\n    ')))
        raise

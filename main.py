import praw
import prawcore
from pprint import pprint
import time
from core.process import process_comment
from core.credentials import CredentialsLoader
from core.regex import REPatterns
from core import constants as consts


credentials = CredentialsLoader().get_credentials()

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
                elif message.subject == "comment reply" and REPatterns.reply_mention.findall(message.body):
                    process_comment(reddit, reddit.comment(message.id))
            else:  # was a message
                # if message.first_message == "None":
                #     message.reply("Sorry, I'm only a bot! I'll contact my creator /u/pmdevita for you.")
                reddit.redditor("pmdevita").message("Someone messaged me!",
                                                    "Subject: " + message.subject + "\n\nContent:\n\n" + message.body)

            reddit.inbox.mark_read([message])

        time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        print("Exiting...")
        break

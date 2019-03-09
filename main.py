import praw
import prawcore
from requests.exceptions import ConnectionError
import time
import traceback
from core.process import process_comment, process_mod_invite
from core.credentials import CredentialsLoader
from core.regex import REPatterns
from core import constants as consts
from core.constants import SUCCESS, USER_FAILURE, UPLOAD_FAILURE
from core.secret import secret_process
from pony.orm.dbapiprovider import OperationalError

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

print("GifReversingBot v{} Ctrl+C to stop".format(consts.version))

mark_read = []
failure_counter = 1  # 1 by default since it is the wait timer multiplier

while True:
    try:
        failure = False
        if mark_read:   # Needed to clear after a Reddit disconnection error
            reddit.inbox.mark_read(mark_read)
            mark_read.clear()
        # for all unread messages
        for message in reddit.inbox.unread():
            # for all unread comments
            if message.was_comment:
                result = None
                # username mentions are simple
                if message.subject == "username mention":
                    result = process_comment(reddit, reddit.comment(message.id))
                # if it was a reply, check to see if it contained a summon
                elif message.subject == "comment reply" or message.subject == "post reply":
                    if REPatterns.reply_mention.findall(message.body):
                        result = process_comment(reddit, reddit.comment(message.id))
                    else:
                        secret_process(reddit, message)
                # Depending on success or other outcomes, we mark the message read
                if result == SUCCESS or result == USER_FAILURE:
                    mark_read.append(message)
                # If the upload failed, try again later
                elif result == UPLOAD_FAILURE:
                    failure = True
                    print("Upload failed, not removing from queue")
                else:
                    mark_read.append(message)
            else:  # was a message
                # if message.first_message == "None":
                #     message.reply("Sorry, I'm only a bot! I'll contact my creator /u/pmdevita for you.")
                if message.subject[:22] == 'invitation to moderate':
                    subreddit = process_mod_invite(reddit, message)
                    if subreddit:
                        reddit.redditor(operator).message("GRB modded!", "GifReversingBot modded in r/{}!".format(subreddit))
                elif message.subject in consts.ignore_messages:
                    pass
                else:
                    reddit.redditor(operator).message("Someone messaged me!",
                                                      "Subject: " + message.subject + "\n\nContent:\n\n" + message.body)
                mark_read.append(message)

        reddit.inbox.mark_read(mark_read)
        mark_read.clear()
        if failure:
            print("An upload failed, extending wait")
            failure_counter += 1
        else:
            failure_counter = 1

        # for sub in modded_subs:
        #     for message in sub.mod.inbox():
        #         if message.subject == consts.subreddit_mod_summon and message.author.name == "AutoModerator":
        #             post_id = REPatterns.reddit_submission.findall(message.body)[0][2]
        #             if post_id:
        #                 process_comment(reddit, reddit.submission(id=post_id))
        #                 message.delete()

        time.sleep(consts.sleep_time * failure_counter)

    except prawcore.exceptions.ResponseException as e:   # Something funky happened
        print("Did a comment go missing?", e, vars(e))
        time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        reddit.inbox.mark_read(mark_read)
        print("Exiting...")
        break

    except OperationalError:
        print("Unable to connect to database")
        reddit.redditor(operator).message("Unable to connect to database")
        time.sleep(consts.sleep_time * 2)

    except ConnectionError:
        print('A connection was unable to be established')
        time.sleep(consts.sleep_time * 2)

    except Exception as e:
        reddit.inbox.mark_read(mark_read)
        if mode == "production":
            reddit.redditor(operator).message("GRB Error!", "Help I crashed!\n\n    {}".format(
                str(traceback.format_exc()).replace('\n', '\n    ')))
        raise

import praw
import prawcore
import time
import traceback
from datetime import datetime, timedelta
from gifreversingbot.core.process import process_comment, process_mod_invite
from gifreversingbot.core.credentials import CredentialsLoader
from gifreversingbot.core.regex import REPatterns
from gifreversingbot.core import constants as consts
from gifreversingbot.core.constants import SUCCESS, USER_FAILURE, UPLOAD_FAILURE
from gifreversingbot.core.secret import secret_process
from gifreversingbot.core.arguments import parser
from gifreversingbot.core.operator import Operator
from pony.orm.dbapiprovider import OperationalError

credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

args = parser.parse_args()

new_operator = Operator(reddit.redditor(operator), credentials['general'].get('testing', "false").lower() == "true")

mark_read = []

cutoff = None
if args.cutoff:
    cutoff = int(args.cutoff)


def main():
    db_connected = True
    failure_counter = 1  # 1 by default since it is the wait timer multiplier
    print(f"{consts.bot_name} v{consts.version} Ctrl+C to stop")

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
                    # Comments that arrive the same time the inbox is being checked may not have an ID?
                    if not message.id:
                        new_operator.message("Message had no ID???")
                    if cutoff:
                        if datetime.utcfromtimestamp(message.created_utc) < datetime.now() - timedelta(days=cutoff):
                            print("Skipping older message")
                            mark_read.append(message)
                            continue    # Skips the 5 message mark read step but probably fine
                    # username mentions are simple
                    if message.subject == "username mention":
                        result = process_comment(reddit, reddit.comment(message.id))
                    # if it was a reply, check to see if it contained a summon
                    elif message.subject == "comment reply" or message.subject == "post reply":
                        if REPatterns.reply_mention.findall(message.body):
                            result = process_comment(reddit, reddit.comment(message.id))
                        else:
                            secret_process(reddit, message)
                            result = SUCCESS
                    new_operator.unset_request_info()
                    # Depending on success or other outcomes, we mark the message read
                    if result == SUCCESS or result == USER_FAILURE:
                        mark_read.append(message)
                    # If the upload failed, try again later
                    elif result == UPLOAD_FAILURE:
                        failure = True
                        print("Upload failed, not removing from queue")
                else:  # was a message
                    if message.subject[:22] == 'invitation to moderate':
                        subreddit = process_mod_invite(reddit, message)
                        if subreddit:
                            new_operator.message(f"{consts.bot_name} modded in r/{subreddit}!", "Modded!")
                    elif message.subject in consts.ignore_messages:
                        pass
                    else:
                        new_operator.message(message.subject + "\n\n---\n\n" + message.body, "Message", False, True)
                    mark_read.append(message)
                if len(mark_read) >= 5:     # Mark read every 5 in a batch to avoid a small chance of disaster
                    reddit.inbox.mark_read(mark_read)
                    mark_read.clear()
                if not db_connected:
                    db_connected = True
                    new_operator.message("The bot was able to reconnect to the database.", "DB Reconnected")
                if credentials['general'].get('testing', "false").lower() == "true":
                    print("Press enter to continue or type something to quit")
                    if len(input()):
                        print("You can now safely end the process")
                        break
            if mark_read:
                reddit.inbox.mark_read(mark_read)
                mark_read.clear()
            if failure:
                print("An upload failed, extending wait")
                # failure_counter += 1
            else:
                failure_counter = 1

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
            if db_connected:
                new_operator.message("The bot has disconnected from the database. If connection is reestablished, a "
                                     "follow-up message will be sent.", "DB Disconnected")
                db_connected = False
            failure_counter = min(failure_counter + 1, 15)
            time.sleep(consts.sleep_time * failure_counter)

        # except ConnectionError:
        #     print('A connection was unable to be established')
        #     time.sleep(consts.sleep_time * 2)

        except Exception as e:
            reddit.inbox.mark_read(mark_read)
            new_operator.message("Help I crashed!\n\n    {}".format(str(traceback.format_exc()).replace('\n', '\n    ')),
                                 "Error!", False)
            raise


if __name__ == '__main__':
    main()
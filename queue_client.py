import praw
import prawcore
from requests.exceptions import ConnectionError
import time
import traceback
import signal
import sys
from core.process import process_comment, process_mod_invite, process_reverse
from core.credentials import CredentialsLoader
from core.context import CommentContext
from core.regex import REPatterns
from core import constants as consts
from core.constants import SUCCESS, USER_FAILURE, UPLOAD_FAILURE
from core.secret import secret_process
from core.queue import Queue
from pony.orm.dbapiprovider import OperationalError


from core.gif import Gif
import random
import string


credentials = CredentialsLoader().get_credentials()

mode = credentials['general']['mode']
operator = credentials['general']['operator']

reddit = praw.Reddit(user_agent=consts.user_agent,
                     client_id=credentials['reddit']['client_id'],
                     client_secret=credentials['reddit']['client_secret'],
                     username=credentials['reddit']['username'],
                     password=credentials['reddit']['password'])

print("GifReversingBot Queue Client v{} Ctrl+C to stop".format(consts.version))

failure_counter = 1  # 1 by default since it is the wait timer multiplier


q = Queue()
q.enter_queue()


def signal_handler(sig, frame):
    print("Exiting...")
    q.exit_queue()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

while True:
    try:
        for i in q.get_jobs():
            print(i, i.origin_host, i.origin_id)
            result = process_reverse(reddit, CommentContext.from_json(reddit, dict(i.context)))
            if result == SUCCESS or result == USER_FAILURE:
                q.remove_job(i)
        time.sleep(consts.sleep_time * failure_counter)

    except prawcore.exceptions.ResponseException as e:   # Something funky happened
        q.exit_queue()
        print("Did a comment go missing?", e, vars(e))
        time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        q.exit_queue()
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        q.exit_queue()
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
        q.exit_queue()
        if mode == "production":
            reddit.redditor(operator).message("GRB Client Error!", "Help I crashed!\n\n    {}".format(
                str(traceback.format_exc()).replace('\n', '\n    ')))
        raise

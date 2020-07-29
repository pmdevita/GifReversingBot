import praw
import core.constants as consts


class Operator:
    """Used for messaging the operating user of the bot"""
    def __init__(self, reddit: praw.Reddit, user, testing_mode):
        self.reddit = reddit
        self.user = reddit.redditor(user)
        self.testing = testing_mode

    def message(self, message, subject="Notification", print_message=True, always_message=False):
        if not self.testing or always_message:
            self.user.message(consts.short_name + " - " + subject, message)
        if print_message:
            print(message)


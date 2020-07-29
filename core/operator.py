from praw.models import Redditor
import core.constants as consts


class Operator:
    user = None
    reddit = None
    testing = None
    """Used for messaging the operating user of the bot"""
    def __init__(self, user: Redditor, testing_mode):
        Operator.user = user
        Operator.testing = testing_mode

    @classmethod
    def instance(cls):
        return cls.__new__(cls)

    def message(self, message, subject="Notification", print_message=True, always_message=False):
        if not Operator.testing or always_message:
            Operator.user.message(consts.short_name + " - " + subject, message)
        if print_message:
            print(message)


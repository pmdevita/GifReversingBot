from praw.models import Redditor
import core.constants as consts
import json


class Operator:
    user = None
    reddit = None
    testing = True  # Set to avoid errors in unit testing, this should be set during startup
    data = None
    """Used for messaging the operating user of the bot"""
    def __init__(self, user: Redditor, testing_mode):
        Operator.user = user
        Operator.testing = testing_mode

    @classmethod
    def instance(cls):
        return cls.__new__(cls)

    @classmethod
    def message(cls, message, subject="Notification", print_message=True, always_message=False):
        if not cls.testing or always_message:
            cls.user.message(consts.short_name + " - " + subject, message)
        if print_message:
            print(message)

    @classmethod
    def context_message(cls, message, subject="Notification", print_message=True, always_message=False):
        if cls.data:
            pretty_data = json.dumps(cls.data, indent=4).replace("\n", "\n    ")
        else:
            pretty_data = "No Data"
        cls.message(f"{message}\n\n---\n\nRequest Data:\n\n    {pretty_data}", subject, False, always_message)
        if print_message:
            print(message)

    @classmethod
    def set_request_info(cls, data):
        cls.data = data

    def unset_request_info(self):
        Operator.data = None


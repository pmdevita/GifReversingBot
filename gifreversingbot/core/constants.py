import importlib.metadata
from gifreversingbot.core.credentials import CredentialsLoader

bot_name = "GifReversingBot"
short_name = "GRB"
version = importlib.metadata.version(__package__.split(".")[0])
user_agent = f"{bot_name} v{version} by /u/pmdevita"
spoof_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0"

sleep_time = 90
username = CredentialsLoader.get_credentials()['reddit']['username']

issue_link = f"https://www.reddit.com/message/compose/?to=pmdevita&subject={bot_name}%20Issue&message=" \
             "Add a link to the gif or comment in your message%2C I%27m not always sure which request is being " \
             "reported. Thanks for helping me out!"

bot_footer = f"---\n\n^(I am a bot.) [^(Report an issue)]({issue_link})"

bot_footer_reversed = f"---\n\n[^(eussi na tropeR)]({issue_link}) ^(.tob a ma I)"

nsfw_reply_template = "##NSFW\n\nHere is your gif!\n{}\n\n" + bot_footer

reply_template = "Here is your gif!\n{}\n\n" + bot_footer

reply_ban_subject = "Here is your gif!"

reply_ban_template = "Hi! Unfortunately, I am banned in that subreddit so I couldn't reply to your comment. " \
                       "I was still able to reverse your gif though!\n{}\n\n" + bot_footer

unnecessary_manual_message = "\n\nJust so you know, you don't have to manually give the gif URL if it is in " \
                             "a parent comment or the post. I would have known what you meant anyways :)\n\n"

reply_reverse_template = "[{}]({})\n!fig ruoy si ereH\n\n" + bot_footer_reversed

ignore_messages = ["Welcome to Moderating!", "re: Here is your gif!", "Your reddit premium subscription has expired."]

MP4 = 'mp4'
GIF = 'gif'
OTHER = 3
LINK = 4
WEBM = 'webm'

GFYCAT = 1
IMGUR = 2
REDDITGIF = 3
REDDITVIDEO = 4
STREAMABLE = 5
LINKGIF = 6

SUCCESS = 0         # Reverse and upload succeeded
USER_FAILURE = 1    # Something about the user's request doesn't make sense (ignore it)
UPLOAD_FAILURE = 2  # The gif failed to upload (try again later)

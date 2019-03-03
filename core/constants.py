from core.credentials import CredentialsLoader

user_agent = "GifReversingBot v{} by /u/pmdevita"
spoof_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0"
imgur_spoof_cookie = CredentialsLoader.get_credentials()['imgur']['imgur_cookie']
version = "2.6.10"
sleep_time = 90
username = CredentialsLoader.get_credentials()['reddit']['username']

bot_footer = "---\n\n^(I am a bot.) [^(Report an issue)]" \
                 "(https://www.reddit.com/message/compose/?to=pmdevita&subject=GifReversingBot%20Issue)"


nsfw_reply_template = "##NSFW\n\nHere is your gif!\n{}\n\n" + bot_footer

reply_template = "Here is your gif!\n{}\n\n" + bot_footer

reply_ban_subject = "Here is your gif!"

reply_ban_template = "Hi! Unfortunately, I am banned in that subreddit so I couldn't reply to your comment. " \
                       "I was still able to reverse your gif though!\n{}\n\n" + bot_footer

unnecessary_manual_message = "\n\nJust so you know, you don't have to manually give the gif URL if it is in " \
                             "a parent comment or the post. I would have known what you meant anyways :)\n\n"

ignore_messages = ["Welcome to Moderating!"]

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

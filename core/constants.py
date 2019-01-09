from core.credentials import CredentialsLoader

user_agent = "vredditshare v{} by /u/pmdevita"
spoof_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0"
imgur_spoof_cookie = CredentialsLoader.get_credentials()['imgur']['imgur_cookie']
version = "0.5"
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


VIDEO = 1
GIF = 2
OTHER = 3
LINK = 4

GFYCAT = 1
IMGUR = 2
REDDITGIF = 3
REDDITVIDEO = 4
STREAMABLE = 5
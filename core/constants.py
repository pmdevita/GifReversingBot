from core.credentials import CredentialsLoader

user_agent = "GifReversingBot v{} by /u/pmdevita"
spoof_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0"
imgur_spoof_cookie = CredentialsLoader.get_credentials()['imgur']['imgur_cookie']
version = "2.6.1"
sleep_time = 120
username = CredentialsLoader.get_credentials()['reddit']['username']

bot_footer = "---\n\n^(I am a bot.) [^(Report an issue)]" \
                 "(https://www.reddit.com/message/compose/?to=pmdevita&subject=GifReversingBot%20Issue)"

reply_template = "Here is your gif!\n{}\n\n" + bot_footer

nsfw_reply_template = "##NSFW\n\nHere is your gif!\n{}\n\n" + bot_footer

ban_message_template = "Hi! Unfortunately, I am banned in that subreddit so I couldn't reply to your comment. " \
                       "I was still able to reverse your gif though!\n{}\n\n" + bot_footer

ban_message_subject = "Here is your gif!"

VIDEO = 1
GIF = 2
OTHER = 3

GFYCAT = 1
IMGUR = 2
REDDITGIF = 3
REDDITVIDEO = 4
STREAMABLE = 5
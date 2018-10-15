import re
from core import constants as consts

class REPatterns:
    # Reddit textpost pattern for avoiding text posts
    textpost = re.compile("^http(?:s)?://(?:\w+?\.)?reddit\.com/r/.*?/comments")

    # Imgur
    # Checks if a link is a Imgur link
    # if_imgur = re.compile("^(?:|http:\/\/|https:\/\/|http:\/\/i\.|https:\/\/i\.|i\.)imgur.com\/")

    # Retrieves an ID from a non gallery Imgur URL
    # imgur = re.compile(
    #     "^(?:|http:\/\/|https:\/\/|http:\/\/i\.|https:\/\/i\.|i\.)imgur.com\/(?!gallery)(.*?)(?:|\..*|\/.*)$")
    # # Retrieves an ID from a gallery Imgur URL
    # imgur_gallery = re.compile(
    #     "^(?:|http://|https://|http://i\.|https://i\.|i\.)imgur.com/(?:gallery/)(.*?)(?:|\..*|/.*)$")

    imgur = re.compile("^http(?:s)?://(?:\w+?\.)?imgur.com/(a/)?(gallery/)?(?(1)(?P<album_id>.{7})|(?(2)(?P<gallery_id>.{7})|(?P<image_id>.{7})))")

    # Gfycat
    gfycat = re.compile("^http(?:s)?://(?:\w+?\.)?gfycat\.com/(?:gifs/detail/)?([a-zA-Z]*)")

    # Reddit Gif
    reddit_gif = re.compile("^http(?:s)?://i.redd.it/(.*?).gif")

    # Reddit Video
    reddit_vid = re.compile("^http(?:s)?://v.redd.it/(.*)")

    # Streamable
    streamable = re.compile("^http(?:s)?://streamable.com/(.*)")

    # Mention in a comment reply
    reply_mention = re.compile("u/{}".format(consts.username.lower()), re.I)

    # Markdown link
    link = re.compile("\[.*?\] *\n? *\((.*?)\)")

    # Reddit submission link
    reddit_submission = re.compile("^http(?:s)?://(?:\w+?\.)?reddit.com/r/(?P<subreddit>.*?)/comments/(?P<thread_id>\w{6})/(?P<post_slug>.*?)")

if __name__ == '__main__':
    print(REPatterns.reddit_submission.findall("https://www.reddit.com/r/holdmybeer/comments/9nn67x/hmb_while_i_jump_over_this_pole/"))
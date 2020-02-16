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

    imgur = re.compile("http(?:s)?://(?:\w+?\.)?imgur.com/(a/)?(gallery/)?(?(1)(?P<album_id>[a-zA-Z0-9]{5,7})|(?(2)(?P<gallery_id>[a-zA-Z0-9]{5,7})|(?P<image_id>[a-zA-Z0-9]{5,7})))(?:\S*)")

    # Gfycat
    gfycat = re.compile("https?://(?:\w+?\.)?gfycat\.com/(?:(?:\S*?/)(?!/))*([a-zA-Z]*)")

    # Reddit Gif
    reddit_gif = re.compile("http(?:s)?://i.redd.it/(.*?)\.gif")

    # Reddit Video
    reddit_vid = re.compile("https?://v.redd.it/(\w+)")

    # Streamable
    streamable = re.compile("https?://streamable.com/([a-z0-9]*)")

    # Mention in a comment reply
    reply_mention = re.compile("u/{}".format(consts.username.lower()), re.I)

    # Markdown link
    link = re.compile("\[.*?\] *\n? *\((.*?)\)")

    # Reddit submission link
    reddit_submission = re.compile("http(?:s)?://(?:\w+?\.)?reddit.com(/r/|/user/)?(?(1)(\w{3,21}))(?(2)/comments/(\w{6})(?:/[\w%]+)?)?(?(3)/(\w{7}))?/?(\?)?(?(5)(.+))?")

    # Gif link
    link_gif = re.compile("(https?://\S*\.gif)")

    # NSFW
    nsfw_text = re.compile("(nsfw)", re.I)

    # Reupload
    reupload_text = re.compile("(reupload|renew)", re.I)


if __name__ == '__main__':
    print(type(REPatterns.reddit_submission.search("Here is your gif!\nhttps://files.catbox.moe/ohpyy5.mp4\n\n---\n\n^(I am a bot.) [^(Report an issue)](https://www.reddit.com/message/compose/?to=pmdevita&subject=GifReversingBot%20Issue&message=Add a link to the gif or comment in your message%2C I'm not always sure which request is being reported. Thanks for helping me out!)").group()))
    r = REPatterns.reddit_submission.findall("https://www.redddit.com/r/pmdevita/comments/bn7x1a/")[0]
    print(r)
    for i in r:
        if i:
            print("hi")



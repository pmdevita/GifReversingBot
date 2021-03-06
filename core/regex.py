import re
from core import constants as consts

class REPatterns:
    # Mention in a comment reply
    reply_mention = re.compile("u/{}".format(consts.username.lower()), re.I)

    # Markdown link
    link = re.compile("\[.*?\] *\n? *\((.*?)\)")

    # NSFW
    nsfw_text = re.compile("(nsfw)", re.I)

    # Reupload
    reupload_text = re.compile("(reupload|renew)", re.I)


if __name__ == '__main__':
    print(REPatterns.link_gif.findall("https://media4.giphy.com/media/VaZps4e5JECKSmtdOH/giphy.gif"))



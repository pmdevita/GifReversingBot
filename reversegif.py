import re
import time
from urllib.request import urlopen

import praw
import prawcore
import validators

import core.hosts.imgur
from core import upload
from core.file import getduration
from core.hosts.gfycat import gfycat
from core.hosts.imgur import ImgurClient
from core.regex import precompiledregex
from core.reverse import reverse_gif, reversemp4
from keys import clientid, clientsecret, username, password, imgurid, imgursecret

safemode = "Off"  # On | Off

useragent = "GifReverser v1.3 by /u/pmdevita"

# Main method
def process_comment(comment):
    # In safe mode, only certified users can interact with the bot
    if safemode is "On":
        if not comment.author.name in ["pmdevita"]:
            return

    print("New Comment by " + comment.author.name)
    print(comment)

    # check if we have already reversed the gif
    ref = getreffedobject(comment)
    parentcheck = historycheck(ref)  # if the history check returns a link, we are just gonna give them that
    if not parentcheck==False:
        print("Wants a rereversed gif. Just gonna link them to the previous one.")
        reply(parentcheck, comment)
        return

    # parentcheck didn't return a link. Its a new gif

    url = geturl(comment)
    if url is None:
        print("Didn't find a URL")
        return
    print(url)
    urldata = geturldata(url)
    if urldata is None:
        print("Could not find any data in URL!")
        return
    print(urldata)
    if urldata[0] == "imvid":  # mp4 way
        mp4 = urlopen(urldata[1])
        reverse = reversemp4(mp4)
        link = upload.imgurvidgif(reverse)
    elif urldata[0] == "imgif":
        gif = urlopen(urldata[1])
        reverse = reverse_gif(gif)
        link = core.hosts.imgur.imgurupload(reverse, "asdf.gif", "image/gif")
    # elif urldata[0] == "gfygif":      # Implementation where we actually reverse the gfycat gif
    #     gif = urlopen(urldata[1])     # Redundant since gfycat already reverses the gif
    #     reverse = reversegif(gif)
    #     link = gfy.UploadFromStream(reverse)
    #     print(link)
    elif urldata[0] == "gfygif":
        link = urldata[1][:-4] + "-reverse.mp4#?direction=reverse"
    elif urldata[0] == "linkgif":
        gif = urlopen(urldata[1])
        reverse = reverse_gif(gif)
        link = core.hosts.imgur.imgurupload(reverse, "asdf.gif", "image/gif")
    else:
        print("Unsupported mode!")
        return
    if not link:
        print("Something happened, can't reply")
    else:
        reply(link, comment)

# Look up the tree and see if this is in response to the bot previously
def historycheck(comment):
    # pprint(vars(comment))
    print(type(comment))
    if comment.author.name==username and not comment.is_root:
        #hey this comment is ours! don't reverse a gif we already reversed

        #get parent of our comment so we can find the previous summon
        parent = getcommentparent(comment)
        #get the gif this comment was referring to
        return geturl(parent)
    return False

# Praw gives extra characters on the front that probably mean something but not helpful here
def getcommentparent(comment):
    return reddit.comment(comment.parent_id[3:])

# Reply to the comment object with the
def reply(link, comment):
    try:
        comment.reply(
            "Here is your gif!\n{}\n\n---\n\n^(I am a bot.) [^(Report an issue)](https://www.reddit.com/message/compose"
            "/?to=pmdevita&subject=GifReversingBot%20Issue)".format(link))
        print("Successfully reversed and replied!")
    except praw.exceptions.APIException as err:
        error = vars(err)
        if err.error_type == "RATELIMIT":
            errtokens = error['message'].split()
            print("Oops! Hit the rate limit! Gotta wait " + errtokens[len(errtokens) - 2] + " " + errtokens[
                len(errtokens) - 1])
            #message the user about the rate limit


def geturldata(url):
    id = ""
    mode = ""
    # check if imgur first
    if cregex.ifimgur.findall(url):
        if cregex.imgur.findall(url):
            id = cregex.imgur.findall(url)[0]
            pic = imgur.get_image(id)
            return imguranalyze(pic)

        elif cregex.imgurg.findall(url):
            id = cregex.imgurg.findall(url)[0]
            pic = imgur.gallery_item(id)
            if str(type(pic)) == "<class 'imgurpython.imgur.models.gallery_image.GalleryImage'>":
                return imguranalyze(pic)  # gallery image
            else:
                return imguranalyze(imgur.get_image(pic.images[0]['id']))  # take first image from gallery album

    # check for gfycat
    if cregex.gfycat.findall(url):
        id = cregex.gfycat.findall(url)[0]
        pic = gfy.get_gfycat(id)
        return gfycatanalyze(pic)

    if cregex.reddit.findall(url):
        return ("linkgif", url)


    return None

def gfycatanalyze(pic):
    # will support mp4 reversing later
    # pic data contains mp4 size which can tell us if we can use mp4 methods
    return ("gfygif", pic["gfyItem"]["mp4Url"])


def imguranalyze(pic):
    # pprint(vars(pic))
    if not pic.animated:
        print("Not a gif!")
        return None

    if pic.mp4_size > 0 and pic.size > 1081587:  # new gifs may not have an mp4 version yet
        duration = getduration(urlopen(pic.mp4))
        if duration <= 0:  # probably a vidgif # WORKAROUND: VidGif is down!
            print("It's 15 seconds. Probably a imvid so we'll put it through that")
            mode = "imvid"
            data = pic.mp4
        else:  # is a large gif. use gif methods
            print("Reversing and uploading as imgif")
            mode = "imgif"
            # data = pic.gifv[:-1] # convert from gif
            data = pic.mp4 # convert from mp4
        return (mode, data)
    else:  # use gif
        print("Reversing and uploading as imgif")
        mode = "imgif"
        data = pic.gifv[:-1]
        return (mode, data)

    return None


def geturl(comment):
    tokens = comment.body.split()

    if len(tokens) >= 2:  # first check for direct request
        for i in tokens:
            if validateurl(i):
                return i
    if comment.is_root:
        if validateurl(comment.submission.url):
            return comment.submission.url
    else:
        for i in getcommentparent(comment).body.split():
            if validateurl(i):
                return i

    return None

# returns post or comment that contains the info the summon comment is referring to



def validateurl(url):
    if validators.url(url) and not re.match(cregex.textpost, url):
        return True
    else:
        return False

def getreffedobject(comment):
    tokens = comment.body.split()
    if len(tokens) >= 2:  # first check for direct request
        for i in tokens:
            if validateurl(i):
                print("direct")
                return comment
    if comment.is_root:
        if validateurl(comment.submission.url):
            return comment.submission
    else:
        parent = getcommentparent(comment)
        for i in parent.body.split():
            if validateurl(i):
                return parent
gfy = gfycat()

reddit = praw.Reddit(user_agent=useragent,
                     client_id=clientid,
                     client_secret=clientsecret,
                     username=username,
                     password=password)
cregex = precompiledregex()
imgur = ImgurClient(imgurid, imgursecret)

if __name__ == "__main__":
    while True:
        try:
            for message in reddit.inbox.unread():
                # pprint(vars(message))
                if message.was_comment:
                    if message.subject == "username mention":
                        process_comment(reddit.comment(message.id))
                else:  # was a message
                    if message.first_message == "None":
                        message.reply("Sorry, I'm only a bot! I'll contact my creator /u/pmdevita for you.")
                    reddit.redditor("pmdevita").message("Someone messaged me!",
                                                        "Subject: " + message.subject + "\n\nContent:\n\n" + message.body)

                reddit.inbox.mark_read([message])
        except prawcore.exceptions.RequestException as e:
            print("Got the weird error", e)
            time.sleep(600)
        time.sleep(120)

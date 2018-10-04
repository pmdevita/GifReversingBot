import os
import time
import urllib
import zlib
from pprint import pprint
from urllib.request import urlopen

import requests

from core.hosts.imgur import imgurupload
# from keys import www, domainlocation, domain
# from core.file import resetfile, getduration
from core import constants as consts


def imgurvidgif(vid, delete=True):
    resetfile(vid)
    filepath = www + domainlocation + ".mp4"
    f = open(filepath, 'wb')
    f.write(vid.read())
    f.close()
    # duration = min(15,getduration(filepath))
    duration = getduration(filepath)
    values = {"source": domain + domainlocation + ".mp4", "start": "0.00", "stop": str(duration-.50),
              "url": domain + domainlocation + ".mp4"}
    # print(values)
    data = urllib.parse.urlencode(values).encode("UTF-8")  # parameters
    # print(data)
    headers = {"Accept": "*/*", "Origin": "http://imgur.com", "X-Requested-With": "XMLHttpRequest",
               "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Accept-Encoding": "gzip, deflate",
               "Accept-Language": "en-US,en;q=0.8"}
    request = urllib.request.Request("http://imgur.com/vidgif/upload", data, headers)
    r = requests.post("https://imgur.com/vidgif/upload", values, headers=headers)
    print(r.json())
    ticket = r.json()['data']['ticket']
    print("Upload ticket", ticket)
    complete = False
    while not complete:
        # request = urllib.request.Request("http://imgur.com/vidgif/poll/" + ticket, headers=headers)
        r = requests.get("https://imgur.com/vidgif/poll/{}".format(ticket), headers=headers)
        response = r.json()
        if response['data']['failed']:
            complete = True
            print("Imgur says the conversion failed")
            return None
        print(response)
        time.sleep(2)

    pprint(response)
    if delete:
        pprint("Delete: 'https://imgur.com/delete/" + response['data']['deletehash'] + "'")
    os.remove(filepath)
    return "https://imgur.com/" + response['data']['hash']


def decodegzip(data):
    return zlib.decompress(data, 16 + zlib.MAX_WBITS).decode()

def imgurapiupload(path):
    """
    :param path: string path to file
    :return:
    """
    print("File size: ", os.path.getsize("temp.gif"))
    if os.path.getsize(reverse) > 10485760:
        print("Oh no! The file is too large to upload! (", round(os.path.getsize(reverse) / 1048576, 2), ")")
        print("Alerting the user...")
        reddit.redditor(comment.author.name).message("Oops!",
                                                     "Sorry! Imgur's API limits me to 10MB and the gif is larger than that. Hopefully, a solution will be found soon.\n\n---\n\n^(I am a bot.) [^(Report an issue)](https://www.reddit.com/message/compose/?to=pmdevita&subject=GifReversingBot%20Issue)")
        return
    else:
        print("Looks small enough, let's upload!")
    uploaddata = imgur.upload_from_path(reverse)
    print("Returned data", uploaddata)
    null = input()


if __name__ == '__main__':
    with open("../temp.gif", "rb") as f:
        imgurupload(f, consts.GIF)
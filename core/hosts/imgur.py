import json
import time

import requests

from imgurpython import ImgurClient as pImgurClient
from imgurpython.client import API_URL
from imgurpython.client import AuthWrapper as pAuthWrapper
from imgurpython.helpers.error import ImgurClientError
from requests_toolbelt import MultipartEncoder

from core import constants as consts
from core.gif import Gif
from keys import imgurpath
from core.credentials import CredentialsLoader

# Bad solution but I don't want to touch this. Rewrite the client
# for our own needs in the future, especially because imgurpython
# is deprecated

class ImgurClientSingleton:
    client = None

    @classmethod
    def get(cls):
        if cls.client is None:
            creds = CredentialsLoader.get_credentials()
            cls.client = ImgurClient(creds['imgur']['imgur_id'], creds['imgur']['imgur_secret'])
        return cls.client


class ImgurClient(pImgurClient):
    def __init__(self, id, secret):
        self.client_id = id
        self.client_secret = secret
        self.auth = None
        self.mashape_key = None

        imcred = self.loadimgur()
        if imcred == None:
            print("Imgur Auth URL: ", self.get_auth_url('pin'))
            null = input()
            pin = input()
            credentials = self.authorize(pin, 'pin')
            self.saveimgur((credentials['access_token'], credentials['refresh_token']))
            self.set_user_auth(credentials['access_token'], credentials['refresh_token'])
            self.auth = AuthWrapper(credentials['access_token'], credentials['refresh_token'], id, secret)
        else:
            self.auth = AuthWrapper(imcred[0], imcred[1], id, secret)

        # self.credits = self.get_credits()

    def loadimgur(self):
        try:
            with open(imgurpath, 'r') as f:
                data = json.load(f)
                if data == None:
                    return None
                else:
                    return data
        except:
            return None

    def saveimgur(self, data):
        with open(imgurpath, 'w') as f:
            json.dump(data, f)


class AuthWrapper(pAuthWrapper):
    def refresh(self):
        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }

        url = API_URL + 'oauth2/token'

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise ImgurClientError('Error refreshing access token!', response.status_code)

        response_data = response.json()
        self.current_access_token = response_data['access_token']

        with open(imgurpath, 'w') as f:
            json.dump((response_data['access_token'], self.refresh_token), f)


def imgurupload(file, type, delete=True):
    """
    :param file: filestream to upload
    :param name: string name of filestream
    :param mimetype: string for mimetype of filestream
    :param delete: boolean of whether to print delete links
    :return: string link to image
    """
    # First, obtain new album to upload to
    tries = 3
    while tries:
        url = "https://imgur.com/upload/checkcaptcha"
        params = {"total_uploads": "1", "create_album": "true"}
        headers = {"Accept": "*/*", "Origin": "https://imgur.com", "X-Requested-With": "XMLHttpRequest",
                   "User-Agent": consts.spoof_user_agent,
                   "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Referer": "https://imgur.com/upload",
                   "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9", "Host": "imgur.com",
                   "cookie": consts.imgur_spoof_cookie}
        print("getting imgur album id...")
        r = requests.post(url, data=params, headers=headers)
        setup = r.json()
        print(setup)
        # input()


        # Now upload the file to our album id
        url = "https://imgur.com/upload"
        headers = {"Accept": "*/*", "Origin": "http://imgur.com",
                   "User-Agent": consts.spoof_user_agent,
                   "Referer": "https://imgur.com/upload",
                   "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9",
                   "cookie": consts.imgur_spoof_cookie}
        if type == consts.VIDEO:
            files = [
                ("new_album_id", setup["data"]["new_album_id"]),
                ("Filedata", ("{}.mp4".format(setup["data"]["new_album_id"]), file, "video/mp4"))]
        elif type == consts.GIF:
            files = [
                ("new_album_id", setup["data"]["new_album_id"]),
                ("Filedata", ("{}.gif".format(setup["data"]["new_album_id"]), file, "image/gif"))]
        else:
            raise Exception("Wrong upload file type")

        print("uploading...")
        m = MultipartEncoder(fields=files)
        headers["Content-Type"] = m.content_type
        r = requests.post(url, headers=headers, data=m)
        upload = r.json()
        print(upload)
        # input()


        if type == consts.GIF:
            image_id = upload["data"]["hash"]
            image_url = "https://imgur.com/{}.gifv".format(image_id)
            print("Done?", image_url, "https://imgur.com/delete/" + upload["data"]["deletehash"])
            image_url = image_url + "\n\nThere's currently an ongoing issue with uploading gifs to Imgur. If this link " \
                                    "doesn't work, please report an issue. Thanks!"
            # input()
            gif = Gif(consts.IMGUR, image_id, url=image_url, log=False)

        elif type == consts.VIDEO:
            # watch ticket to get link
            url = "https://imgur.com/upload/poll"
            headers = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest",
                       "User-Agent": consts.spoof_user_agent,
                       "Referer": "https://imgur.com/upload",
                       "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9",
                        "cookie": consts.imgur_spoof_cookie}
            params = {"tickets[]": upload["data"]["ticket"]}
            print("waiting for processing...")
            r = requests.get(url, params, headers=headers)
            ticket = r.json()
            print(r.text)
            image_id = None
            while ticket["success"] == True:
                if ticket["data"]["done"]:
                    image_id = r.json()["data"]["done"][upload["data"]["ticket"]]
                    break
                elif ticket["success"] == False:
                    return None
                time.sleep(5)
                r = requests.get(url, params, headers=headers)
                ticket = r.json()
                print(r.text)
            if not image_id:
                tries -= 1
                if tries:
                    file.seek(0)
                    time.sleep(5)
                    continue
                else:
                    return None

            # TODO: once gif uploading is fixed, unindent this
            image_url = "https://imgur.com/{}.gifv".format(image_id)
            gif = Gif(consts.IMGUR, image_id, url=image_url)
        print("Done!")
        return gif
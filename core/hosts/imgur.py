import time
import re
import requests
import json.decoder

from imgurpython import ImgurClient as pImgurClient
from imgurpython.client import API_URL
from imgurpython.client import AuthWrapper as pAuthWrapper
from imgurpython.helpers.error import ImgurClientError
from requests_toolbelt import MultipartEncoder
from imgurpython.imgur.models.gallery_image import GalleryImage

from core import constants as consts
from core.gif import Gif as OldGif
from core.credentials import CredentialsLoader
from core.hosts import GifHost, Gif
from core.regex import REPatterns


class ImgurHost(GifHost):
    name = "Imgur"
    regex = REPatterns.imgur
    url = "https://imgur.com/{}.gifv"

    @classmethod
    def get_id(cls, regex):
        imgur = ImgurClient.get()
        # Retrieve the ID
        imgur_match = regex[0]
        if imgur_match[4]:  # Image match
            id = imgur_match[4]
        elif imgur_match[3]:  # Gallery match
            gallery = imgur.gallery_item(imgur_match[3])
            if not isinstance(gallery, GalleryImage):
                id = gallery.images[0]['id']
            else:
                id = gallery.id
        elif imgur_match[2]:  # Album match
            album = imgur.get_album(imgur_match[2])
            id = album.images[0]['id']

        try:
            pic = imgur.get_image(id)  # take first image from gallery album
        except ImgurClientError as e:
            print("Imgur returned 404, deleted image?")
            if e.status_code == 404:
                return None

        return id

    @classmethod
    def get_gif(cls, id=None, regex=None, url=None):
        if url:
            regex = cls.regex.findall(url)
        if regex:
            gif_id = cls.get_id(regex)
        if gif_id:
            return Gif(cls, gif_id, cls.url.format(gif_id))

class ImgurClient(pImgurClient):
    instance = None

    def __init__(self, id, secret):
        self.client_id = id
        self.client_secret = secret
        self.auth = None
        self.mashape_key = None

        access = CredentialsLoader.get_credentials()['imgur'].get('access_token', None)
        refresh = CredentialsLoader.get_credentials()['imgur'].get('refresh_token', None)
        # imgur_credentials = self.loadimgur()
        if access and refresh:
            self.auth = AuthWrapper(access, refresh, id, secret)
        else:
            # Oauth setup
            print("Imgur Auth URL: ", self.get_auth_url('pin'))
            pin = input("Paste the pin here:")
            credentials = self.authorize(pin, 'pin')
            CredentialsLoader.set_credential('imgur', 'access_token', credentials['access_token'])
            CredentialsLoader.set_credential('imgur', 'refresh_token', credentials['refresh_token'])

            # self.saveimgur((credentials['access_token'], credentials['refresh_token']))

            self.set_user_auth(credentials['access_token'], credentials['refresh_token'])
            self.auth = AuthWrapper(credentials['access_token'], credentials['refresh_token'], id, secret)

        # self.credits = self.get_credits()

    @classmethod
    def get(cls):
        if not cls.instance:
            credentials = CredentialsLoader.get_credentials()
            cls.instance = cls(credentials['imgur']['imgur_id'], credentials['imgur']['imgur_secret'])
        return cls.instance



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

        CredentialsLoader.set_credential('imgur', 'access_token', response_data['access_token'])


def imgurupload(file, type, nsfw=False):
    """
    :param file: filestream to upload
    :param name: string name of filestream
    :param mimetype: string for mimetype of filestream
    :param delete: boolean of whether to print delete links
    :return: string link to image
    """
    # First, obtain new album to upload to
    sleep = 60
    tries = 4
    while tries:
        url = "https://imgur.com/upload/checkcaptcha"
        params = {"total_uploads": "1", "create_album": "true"}
        headers = {"Accept": "*/*", "Origin": "https://imgur.com", "X-Requested-With": "XMLHttpRequest",
                   "User-Agent": consts.spoof_user_agent,
                   "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Referer": "https://imgur.com/upload",
                   "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9", "Host": "imgur.com",
                   "cookie": consts.imgur_spoof_cookie}
        print("getting imgur album id... ", end="")
        r = requests.post(url, data=params, headers=headers)
        try:
            setup = r.json()
        except json.decoder.JSONDecodeError as e:
            if "Imgur is over capacity!" in r.text:
                print("Imgur is over capacity!")
                if tries:
                    time.sleep(sleep)
                    sleep = sleep * 2
                    tries -= 1
                    continue
                else:
                    print("Imgur not responding, upload failed!")
                    return Done
            print("I have no idea what's going on")
            print(r.text)
            input()

        print(setup['data']['new_album_id'])
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

        print("uploading... ", end="")
        m = MultipartEncoder(fields=files)
        headers["Content-Type"] = m.content_type
        r = requests.post(url, headers=headers, data=m)
        try:
            upload = r.json()
        except json.decoder.JSONDecodeError as e:
            if "Imgur is over capacity!" in r.text:
                print("Imgur is over capacity!")
                if tries:
                    time.sleep(sleep)
                    sleep = sleep * 2
                    tries -= 1
                    continue
                else:
                    print("Imgur not responding, upload failed!")
                    return Done

        print("received wait ticket:", upload['data']['ticket'])

        if type == consts.GIF:
            image_id = upload["data"]["hash"]
            image_url = "https://i.imgur.com/{}.gifv".format(image_id)
            final_url = None

            # Did the upload actually publish?
            headers = {"User-Agent": consts.spoof_user_agent}
            # Follow redirect to post URL
            r = requests.get(image_url, headers=headers)
            print(r.url)
            if r.url == "https://i.imgur.com/removed.png":
                print("GIFV DID NOT GENERATE")
                # Try gif URL
                image_url = "https://i.imgur.com/{}.gif".format(image_id)
                final_url = image_url
                headers = {"User-Agent": consts.spoof_user_agent}
                # Follow redirect to post URL
                r = requests.get(image_url, headers=headers)
                print(r.url)
                if r.url == "https://i.imgur.com/removed.png":
                    print("IMGUR GIF UPLOAD FAILURE")
                    tries -= 1
                    if tries:
                        file.seek(0)
                        time.sleep(30)
                        continue
                    else:
                        return None
                else:
                    print("GIF LINK DOES WORK THOUGH")

            print("Done?", image_url, "https://imgur.com/delete/" + upload["data"]["deletehash"])
            # image_url = image_url + "\n\nThere's currently an ongoing issue with uploading gifs to Imgur. If this link " \
            #                        "doesn't work, please report an issue. Thanks!"
            # input()
            gif = OldGif(consts.IMGUR, image_id, url=final_url, log=True, nsfw=nsfw)

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
            try:
                ticket = r.json()
            except json.decoder.JSONDecodeError as e:
                if "Imgur is over capacity!" in r.text:
                    print("Imgur is over capacity!")
                    if tries:
                        time.sleep(sleep)
                        sleep = sleep * 2
                        tries -= 1
                        continue
                    else:
                        print("Imgur not responding, upload failed!")
                        return Done
                print("I have no idea what's going on")
                print(r.text)
                input()

            print(r.text)
            checks = 13
            image_id = None
            while ticket["success"] == True:
                if ticket["data"]["done"]:
                    image_id = r.json()["data"]["done"][upload["data"]["ticket"]]
                    break
                checks -= 1
                if not checks:
                    image_id = None
                    break
                time.sleep(5)
                r = requests.get(url, params, headers=headers)
                try:
                    ticket = r.json()
                except json.decoder.JSONDecodeError as e:
                    if "Imgur is over capacity!" in r.text:
                        print("Imgur is over capacity!")
                        if tries:
                            time.sleep(sleep)
                            sleep = sleep * 2
                            tries -= 1
                            continue
                        else:
                            print("Imgur not responding, upload failed!")
                            return Done
                    print("I have no idea what's going on")
                    print(r.text)
                    input()
                print(r.text)
            if not image_id:
                print("IMGUR TIMED OUT")
                tries -= 1
                if tries:
                    file.seek(0)
                    time.sleep(30)
                    continue
                else:
                    print("IMGUR UPLOAD FAILURE")
                    return None

            # TODO: once gif uploading is fixed, unindent this
            # image_url = "https://imgur.com/{}.gifv".format(image_id)
            gif = OldGif(consts.IMGUR, image_id, nsfw=nsfw)
        print("Done!")
        return gif


if __name__ == '__main__':
    headers = {"User-Agent": consts.spoof_user_agent}
    # Follow redirect to post URL
    r = requests.get("https://imgur.com/Ttg37Fd.gifv", headers=headers)
    if r.url == "https://i.imgur.com/removed.png":
        pass    # failure
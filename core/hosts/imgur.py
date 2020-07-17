import urllib
import time
import requests
import json
from io import BytesIO
from pprint import pprint
from requests_toolbelt.multipart.encoder import MultipartEncoder

from core.credentials import CredentialsLoader
from core import constants as consts
from core.hosts import GifHost, Gif, GifFile, NO_NSFW
from core.regex import REPatterns
from core.file import get_duration, is_valid


class InvalidRefreshToken(Exception):
    def __init__(self):
        super(InvalidRefreshToken, self).__init__("The provided refresh token was invalid")


class ImgurFailedRequest(Exception):
    def __init__(self):
        super(ImgurFailedRequest, self).__init__("Something went wrong with the request")


class ImgurClient:
    instance = None
    CREDENTIALS_BLOCK = 'imgur'
    SERVICE_NAME = "Imgur"
    OAUTH_BASE = "https://api.imgur.com/oauth2/"
    AUTHORIZATION_URL = "authorize"
    TOKEN_URL = "token"
    API_BASE = "https://api.imgur.com/3/"
    GALLERY_ALBUM = "gallery/album/"
    IMAGE = "image/"
    ALBUM = "album/"
    UPLOAD = "upload"

    def __init__(self):
        creds = CredentialsLoader.get_credentials()[self.CREDENTIALS_BLOCK]
        self.client_id = creds["imgur_id"]
        self.client_secret = creds["imgur_secret"]
        self.access = creds.get('access_token', None)
        self.refresh = creds.get('refresh_token', None)
        self.timeout = int(creds.get('token_expiration', 0))

        if self.refresh is None:
            self.authenticate()
        if self.access is None:
            self.get_token()

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def authenticate(self):
        print("Log into {}".format(self.SERVICE_NAME))
        print("Authorize here: " +
              self.OAUTH_BASE + self.AUTHORIZATION_URL + "?" + urllib.parse.urlencode({
                  "client_id": self.client_id, "response_type": "token", "state": "GifHostLibrary"
              }))
        result = input().strip()
        parts = urllib.parse.urlparse(result)
        params = urllib.parse.parse_qs(parts.fragment)
        print(parts, params)

        self.timeout = int(time.time()) + int(params["expires_in"][0])  # [0] quirk of parse_qs
        self.access = params["access_token"][0]
        self.refresh = params["refresh_token"][0]
        CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'refresh_token', self.refresh)
        CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'access_token', self.access)
        CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'token_expiration', str(self.timeout))

    def get_token(self):
        # If the token has expired, request a new one
        if self.timeout < int(time.time()):
            data = {"grant_type": "refresh_token", "client_id": self.client_id,
                    "client_secret": self.client_secret, "refresh_token": self.refresh}
            # For some dumb reason, data has to be a string
            r = requests.post(self.OAUTH_BASE + self.TOKEN_URL, data=data, headers={'User-Agent': consts.user_agent})
            try:
                response = r.json()
            except json.decoder.JSONDecodeError as e:
                print(r.text)
                raise
            # Sometimes (maybe?) Imgur randomly invalidates refresh tokens >:(
            if r.status_code == 401:
                raise InvalidRefreshToken
            self.timeout = int(time.time()) + response["expires_in"]
            self.access = response["access_token"]
            self.refresh = response["refresh_token"]
            CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'access_token', self.access)
            CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'refresh_token', self.refresh)
            CredentialsLoader.set_credential(self.CREDENTIALS_BLOCK, 'token_expiration', str(self.timeout))
        return self.access

    def get_request(self, url, params=None):
        # headers = {'Authorization': "Bearer " + self.get_token()}
        headers = {'Authorization': "Client-ID " + self.client_id}
        r = requests.get(self.API_BASE + url, headers=headers, params=params)
        if r.status_code != 200:
            raise ImgurFailedRequest
        return r

    def post_request(self, url, data, headers=None, params=None):
        full_headers = {'Authorization': "Bearer " + self.get_token()}
        # full_headers = {'Authorization': "Client-ID " + self.client_id}
        if headers:
            full_headers = {**full_headers, **headers}
        r = requests.post(self.API_BASE + url, headers=full_headers, data=data, params=params)
        if r.status_code != 200:
            raise ImgurFailedRequest
        return r

    def options_request(self, url, headers={}):
        full_headers = {'Authorization': "Client-ID " + self.client_id}
        if headers:
            full_headers = {**full_headers, **headers}
        r = requests.options(self.API_BASE + url, headers=full_headers)
        if r.status_code != 200:
            raise ImgurFailedRequest
        return r

    def gallery_item(self, id):
        r = self.get_request(self.GALLERY_ALBUM + id)
        return r.json()['data']

    def get_album(self, id):
        r = self.get_request(self.ALBUM + id)
        return r.json()['data']

    def get_image(self, id):
        r = self.get_request(self.IMAGE + id)
        return r.json()['data']

    def upload_image(self, file, media_type, nsfw, audio=False):
        file.seek(0)

        api = None
        params = None
        data = {"type": "file"}
        if media_type == consts.MP4 or media_type == consts.WEBM:
            data['video'] = ("video." + media_type, file, "video/" + media_type)
            data['name'] = "video." + media_type
            api = self.UPLOAD
            m = MultipartEncoder(fields=data)
            r = self.post_request(api, m, {'Content-Type': m.content_type})
        # We get around the image file size restriction by using a client ID made by a browser
        # Luckily the API is similarish (rather than last time where it wasn't and also 3 steps)
        elif media_type == consts.GIF:
            data['image'] = ("image.gif", file, "image/gif")
            data['name'] = "image.gif"
            api = self.UPLOAD
            params = {'client_id': CredentialsLoader.get_credentials()[self.CREDENTIALS_BLOCK]['imgur_web_id']}
            m = MultipartEncoder(fields=data)
            r = requests.post(self.API_BASE + api, headers={'Content-Type': m.content_type}, data=m, params=params)
        # pprint(r.json())
        j = r.json()
        if not j['data'].get('id', False):
            print(j)
        return j['data']['id']


imgur = ImgurClient.get()


class ImgurGif(Gif):
    process_id = True

    def _get_id(self, id, url):
        """Imgur has a few types of IDs so we need to parse for the one we want"""
        if isinstance(id, list):
            imgur_match = id
        elif isinstance(id, str):
            return id
        else:
            imgur_match = REPatterns.imgur.findall(url)[0]
        id = None
        # Try block for catching imgur 404s
        try:
            if imgur_match[4]:  # Image match
                self.pic = imgur.get_image(imgur_match[4])
            elif imgur_match[3]:  # Gallery match
                gallery = imgur.gallery_item(imgur_match[3])
                # if not isinstance(gallery, GalleryImage):
                self.pic = gallery["images"][0]  # First image from gallery album
                # else:
                #     id = gallery.id
            elif imgur_match[2]:  # Album match
                self.pic = imgur.get_album(imgur_match[2])["images"][0]

            id = self.pic["id"]

        except ImgurFailedRequest as e:
            print("Imgur returned 404, deleted image?")
            self.pic = None
            id = None

        return id

    def analyze(self) -> bool:
        """Analyze an imgur gif using the imgurpython library and determine how to reverse and upload"""

        if not self.pic:
            return False
        # pprint(self.pic)

        if not self.pic['animated']:
            print("Not a gif!")
            return False
        r = requests.get(self.pic['mp4'])
        file = BytesIO(r.content)
        self.duration = get_duration(file)

        self.files.append(GifFile(file, host=self.host, gif_type=consts.MP4, duration=self.duration,
                                  size=self.pic['mp4_size']/1000000))

        # If the file type is a gif, add it as an option and prioritize it
        if self.pic['type'] == 'image/gif':
            r = requests.get(self.pic['gifv'][:-1])
            gif = BytesIO(r.content)
            if is_valid(gif):
                gif_file = GifFile(gif, host=self.host, gif_type=consts.GIF, duration=self.duration)
            # else:
            #     gif_file = GifFile(file, host=self.host, gif_type=consts.GIF, duration=self.duration)
                print("added gif file")
                self.files.insert(0, gif_file)
        print(self.files)
        return True



class ImgurHost(GifHost):
    name = "Imgur"
    regex = REPatterns.imgur
    url_template = "https://imgur.com/{}.gifv"
    gif_type = ImgurGif
    vid_len_limit = 60
    vid_size_limit = 200
    gif_size_limit = 201

    @classmethod
    def upload(cls, file, gif_type, nsfw, audio=False):
        id = imgur.upload_image(file, gif_type, nsfw=nsfw)
        if id:
            return ImgurGif(cls, id, nsfw=nsfw)


if __name__ == '__main__':
    headers = {"User-Agent": consts.spoof_user_agent}
    # Follow redirect to post URL
    r = requests.get("https://imgur.com/Ttg37Fd.gifv", headers=headers)
    if r.url == "https://i.imgur.com/removed.png":
        pass    # failure


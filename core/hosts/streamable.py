import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from core.credentials import CredentialsLoader
from core import constants as consts
from core.gif import Gif
from core.hosts import GifHost
from core.regex import REPatterns


class StreamableHost(GifHost):
    name = "Streamable"
    regex = REPatterns.streamable
    url_template = "https://streamable.com/{}"
    can_gif = False
    can_vid = False


class StreamableClient:
    instance = None

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def __init__(self):
        creds = CredentialsLoader.get_credentials()['streamable']
        self.auth = (creds['email'], creds['password'])
        self.headers = {'User-Agent': consts.user_agent}

    def download_video(self, id):
        r = requests.get('https://api.streamable.com/videos/{}'.format(id), headers=self.headers, auth=self.auth)
        return "https:{}".format(r.json()['files']['mp4']['url'])

    def upload_file(self, filestream, title):
        # tries = 3
        # while tries:
        files = {"file": filestream}
        data = None
        if title:
            data = {'title': title}
        # m = MultipartEncoder(fields=files)
        print("Uploading to streamable...")
        r = requests.post('https://api.streamable.com/upload', headers=self.headers, files=files, data=data, auth=self.auth)
        if r.text:
            return r.json()['shortcode']

    def upload_link(self, link, title):
        r = requests.get('https://api.streamable.com/import', headers=self.headers, params={'url': link, 'title': title}, auth=self.auth)
        print(r.text)
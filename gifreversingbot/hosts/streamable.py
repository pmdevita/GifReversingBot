import requests
import re
from io import BytesIO
from gifreversingbot.core.credentials import CredentialsLoader
from gifreversingbot.core import constants as consts
from gifreversingbot.hosts import GifFile, Gif, GifHost


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
        if r.status_code == 404:
            return None
        json = r.json()
        return r.json()['files']['mp4']

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

streamable = StreamableClient()

class StreamableGif(Gif):
    def analyze(self):
        info = streamable.download_video(self.id)
        if not info:
            return False
        file = BytesIO(requests.get(info['url']).content)
        self.files.append(GifFile(file, host=self.host, gif_type=consts.MP4, audio=False, duration=info['duration'],
                                  size=info['size']/1000000))
        return True


class StreamableHost(GifHost):
    name = "Streamable"
    regex = re.compile("https?://streamable.com/([a-z0-9]*)")
    url_template = "https://streamable.com/{}"
    audio = True
    gif_type = StreamableGif
    can_gif = False
    can_vid = False


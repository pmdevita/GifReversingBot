import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from io import BytesIO
from core.credentials import CredentialsLoader
from core import constants as consts
from core.hosts import GifHost, Gif, GifFile
from core.regex import REPatterns

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
        file = BytesIO(requests.get("https:" + info['url']).content)
        self.files.append(GifFile(file, host=self.host, gif_type=consts.MP4, audio=False, duration=info['duration'],
                                  size=info['size']/1000000))
        return True


class StreamableHost(GifHost):
    name = "Streamable"
    regex = REPatterns.streamable
    url_template = "https://streamable.com/{}"
    audio = True
    gif_type = StreamableGif
    can_gif = False
    can_vid = False


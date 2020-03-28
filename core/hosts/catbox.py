import requests
from requests_toolbelt import MultipartEncoder
import re
from io import BytesIO

from core.hosts import GifHost, Gif, GifFile
from core.credentials import CredentialsLoader
from core import constants as consts
from core.file import is_valid

catbox_hash = CredentialsLoader.get_credentials()['catbox']['hash']

class CatboxGif(Gif):
    process_id = True

    def _get_id(self, id, url):
        # Safety check
        if id:
            ext = id.split(".")[-1]
        else:
            ext = url.split(".")[-1]
            id = self.host.regex.findall(url)[0]
        if ext.lower() in [consts.MP4, consts.GIF, consts.WEBM]:
            # We should do file checks for safety because we could actually get some kind of nasty file
            return id
        return None

    def analyze(self):
        r = requests.get(self.url)
        file = BytesIO(r.content)
        if not is_valid(file):
            return False
        file = GifFile(file, self.host, consts.GIF)
        self.files.append(file)
        vid_file = GifFile(file, self.host, self.id.split(".")[-1], audio=False)
        if self.id[-3:] == consts.GIF:
            self.files.append(vid_file)
        else:
            self.files.insert(0, vid_file)
        return True


class CatboxHost(GifHost):
    name = "Catbox"
    regex = re.compile("https?://files\.catbox\.moe/([a-zA-Z0-9]*\.[a-zA-Z0-9]{3,4})")
    priority = 3
    gif_type = CatboxGif
    audio = True
    url_template = "https://files.catbox.moe/{}"
    vid_size_limit = 200
    gif_size_limit = 20

    @classmethod
    def upload(cls, file, gif_type, nsfw, audio=False):
        file.seek(0)
        mimetype = "image/gif" if gif_type == consts.GIF else "video/" + gif_type
        files = {'reqtype': 'fileupload', 'userhash': catbox_hash, 'fileToUpload': ("file.{}".format(gif_type),
                                                                                     file, mimetype)}
        m = MultipartEncoder(fields=files)
        r = requests.post("https://catbox.moe/user/api.php", data=m, headers={'Content-Type': m.content_type,
                                                                              'User-Agent': consts.user_agent})
        if r.status_code == 200:
            return CatboxGif(cls, None, url=r.text)
        else:
            return None

    @classmethod
    def delete(cls, gif):
        """Accepts a single Gif or a list of Gifs"""
        if isinstance(gif, Gif):
            gif = [gif]
        print(" ".join([g.id for g in gif]))
        r = requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'deletefiles', 'userhash': catbox_hash,
                                                                   'files': " ".join([g.id for g in gif])})
        print(r.content)
        return True



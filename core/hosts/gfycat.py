import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
from math import ceil

from core.credentials import CredentialsLoader
from core import constants as consts
from core.gif import Gif
from core.hosts import GifHost
from core.regex import REPatterns

ENCODE_TIMEOUT = 3200
WAIT = 7
ENCODE_LOOPS = ceil(ENCODE_TIMEOUT / WAIT)

class GfycatHost(GifHost):
    name = "Gfycat"
    regex = REPatterns.gfycat
    url = "https://gfycat.com/{}"


class Gfycat:
    instance = None

    def __init__(self):
        creds = CredentialsLoader.get_credentials()['gfycat']
        self.gfypath = creds["gfypath"]
        self.gfyid = creds["gfycat_id"]
        self.gfysecret = creds["gfycat_secret"]
        self.username = creds.get('username', None)
        self.password = creds.get('password', None)
        self.token = creds.get('refresh_token', None)
        self.timeout = int(creds.get('token_expiration', 0))

        # self.timeout, self.token = self._load_data()

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def _load_data(self):
        try:
            with open(self.gfypath, 'r') as f:
                data = json.load(f)
                if data is None:
                    return 0, ""
                else:
                    return data
        except:
            return 0, ""

    def _save_data(self):
        with open(self.gfypath, "w") as f:
            json.dump((self.timeout, self.token), f)

    def get_token(self):
        # If the token has expired, request a new one
        if self.timeout < int(time.time()):
            # For some dumb reason it has to be a string
            data = {"grant_type": "client_credentials", "client_id": self.gfyid,
                    "client_secret": self.gfysecret}
            if self.username:
                data['grant_type'] = 'password'
                data['username'] = self.username
                data['password'] = self.password

            url = "https://api.gfycat.com/v1/oauth/token"
            r = requests.post(url, data=str(data), headers={'User-Agent': consts.user_agent})
            try:
                response = r.json()
            except json.decoder.JSONDecodeError as e:
                print(r.text)
                raise
            self.timeout = int(time.time()) + response["expires_in"]
            self.token = response["access_token"]
            CredentialsLoader.set_credential('gfycat', 'refresh_token', self.token)
            CredentialsLoader.set_credential('gfycat', 'token_expiration', str(self.timeout))
        return self.token

    def get_gfycat(self, id):
        headers = {"Authorization": "Bearer {}".format(self.get_token())}
        url = "https://api.gfycat.com/v1/gfycats/{}".format(id)
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise Exception("Gfycat - get problem status code {}".format(str(r.status_code)))
        return r.json()

    def upload(self, filestream, media_type, nsfw=False, audio=False, title=None, description=None):
        # If we hit a problem, restart this segment
        tries = 3
        while tries:
            # get gfyname
            url = "https://api.gfycat.com/v1/gfycats"
            headers = {"Authorization": "Bearer " + self.get_token(), 'User-Agent': consts.user_agent,
                       'Content-Type': 'application/json'}
            params = {}
            if media_type == consts.LINK:
                params['fetchUrl'] = filestream
            if description:
                params['description'] = description
            if title:
                params['title'] = title
            if nsfw:
                params["nsfw"] = 1
            if audio:
                params['keepAudio'] = True
            print("getting gfyname...")
            r = requests.post(url, headers=headers, data=str(params))
            # print(r.text)
            metadata = r.json()

            # upload
            if media_type != consts.LINK:
                url = "https://filedrop.gfycat.com"
                if media_type == consts.MP4 or media_type == consts.WEBM:
                    files = {"key": metadata["gfyname"], "file": (metadata["gfyname"], filestream, "video/" + media_type)}
                elif media_type == consts.GIF:
                    files = {"key": metadata["gfyname"], "file": (metadata["gfyname"], filestream, "image/gif")}
                m = MultipartEncoder(fields=files)
                print("uploading...")
                r = requests.post(url, data=m, headers={'Content-Type': m.content_type, 'User-Agent': consts.user_agent})

            # check status for gif's id
            url = "https://api.gfycat.com/v1/gfycats/fetch/status/" + metadata["gfyname"]
            headers = {'User-Agent': consts.user_agent}
            print("waiting for encode...", end=" ")
            r = requests.get(url, headers=headers)
            try:
                ticket = r.json()
            except json.decoder.JSONDecodeError as e:
                print(r.text)
                raise
            # Sometimes we have to wait
            percentage = 0
            for i in range(ENCODE_LOOPS):
                if ticket["task"] == "encoding":
                    time.sleep(WAIT)
                    r = requests.get(url, headers=headers)
                    ticket = r.json()
                    # print(ticket)
                    if float(ticket.get('progress', 0)) > percentage:
                        percentage = float(ticket['progress'])
                        print(percentage, end=" ")
                else:
                    break
            # If there was something wrong, we loop back and try again
            if ticket["task"] == "NotFoundo" or ticket["task"] == "error":
                print("Error uploading? Trying again", ticket)
                tries -= 1
                if tries:
                    if media_type != consts.LINK:
                        filestream.seek(0)
                    time.sleep(5)
                    continue
                else:
                    break
            elif ticket['task'] == 'encoding':
                print("Upload timed out? Trying again", ticket)
                tries -= 1
                if tries:
                    if media_type != consts.LINK:
                        filestream.seek(0)
                    time.sleep(5)
                    continue
                else:
                    break
            if "gfyName" in ticket:
                image_id = ticket["gfyName"]
            elif "gfyname" in ticket:
                image_id = ticket["gfyname"]
            print("Done!")
            break

        if tries:
            return Gif(consts.GFYCAT, image_id, nsfw=nsfw)
        else:
            return None


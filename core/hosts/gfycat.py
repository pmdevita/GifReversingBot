import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
from pprint import pprint

from core.credentials import CredentialsLoader
from core import constants as consts
from core.gif import Gif

class GfycatSingleton:
    client = None

    @classmethod
    def get(cls):
        if cls.client is None:
            cls.client = Gfycat()
        return cls.client


class Gfycat:
    def __init__(self):
        self.timeout, self.token = self._load_data()

    def _load_data(self):
        creds = CredentialsLoader.get_credentials()["gfycat"]
        self.gfypath = creds["gfypath"]
        self.gfyid = creds["gfycat_id"]
        self.gfysecret = creds["gfycat_secret"]
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
        if self.timeout < int(time.time()):
            data = "{'grant_type': 'client_credentials', " \
                   "'client_id': '" + self.gfyid + "','client_secret': '" + self.gfysecret + "'}"
            url = "https://api.gfycat.com/v1/oauth/token"
            r = requests.post(url, data=data)
            response = r.json()
            self.timeout = int(time.time()) + response["expires_in"]
            self.token = response["access_token"]
            self._save_data()
        return self.token

    def get_gfycat(self, id):
        headers = {"Authorization": "Bearer {}".format(self.get_token())}
        url = "https://api.gfycat.com/v1/gfycats/{}".format(id)
        r = requests.get(url, headers=headers)
        return r.json()


    def upload(self, filestream, type, nsfw=False):
        # If we hit a problem, restart this segment
        tries = 3
        while tries:
            # get gfyname
            url = "https://api.gfycat.com/v1/gfycats"
            headers = {"Authorization": "Bearer " + self.get_token(), "Content-Type": "application/json"}
            params = {}
            if nsfw:
                params["nsfw"] = 1
            print("getting gfyname...")
            r = requests.post(url, headers=headers, data=params)
            metadata = r.json()


            # upload
            url = "https://filedrop.gfycat.com"
            data = {"key": metadata["gfyname"]}
            if type == consts.VIDEO:
                files = {"key": metadata["gfyname"], "file": (metadata["gfyname"], filestream, "image/mp4")}
            elif type == consts.GIF:
                files = {"key": metadata["gfyname"], "file": (metadata["gfyname"], filestream, "image/gif")}
            m = MultipartEncoder(fields=files)
            print("uploading...")
            r = requests.post(url, data=m, headers={'Content-Type': m.content_type})

            # check status for gif's id
            url = "https://api.gfycat.com/v1/gfycats/fetch/status/" + metadata["gfyname"]
            print("waiting for encode...")
            r = requests.get(url)
            ticket = r.json()
            print(ticket)
            # Sometimes we have to wait
            wait = 7
            while ticket["task"] == "encoding":
                time.sleep(wait)
                r = requests.get(url)
                ticket = r.json()
                print(ticket)
            # If there was something wrong, we loop back and try again
            if ticket["task"] == "NotFoundo":
                print("Error uploading? Trying again")
                tries -= 1
                if tries:
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
import json
import subprocess
import os
from io import BytesIO

# These functions need to be combined for optimization and cleanliness
# They are doing a lot of the sames stuff already so it's turned into a mess


def get_duration(filestream):
    filestream.seek(0)
    p = subprocess.Popen(
        ["ffprobe", "-i", "pipe:0", "-v", "quiet", "-print_format", "json", "-show_format"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output = p.communicate(input=filestream.read())[0].decode("utf-8")
    data = json.loads(output)
    if not data.get('format', {}).get('duration', None):
        # Can happen sometimes if the file isn't on the drive
        with open('tempfile', 'wb') as f:
            filestream.seek(0)
            f.write(filestream.read())
        p = subprocess.Popen(
            ["ffprobe", "-i", "tempfile", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output = p.communicate()[0].decode("utf-8")
        data = json.loads(output)
        os.remove('tempfile')
    if data['format'].get('duration', None):
        return float(data['format']['duration'])
    return 0


def resetfile(file):
    #print(type(file))
    if not str(type(file)) == "<class 'http.client.HTTPResponse'>":
        #print(file.tell())
        if not file.tell() == 0:
            #print("seeking")
            file.seek(0)


def get_fps(filestream, ffprobe_path="ffprobe"):
    filestream.seek(0)
    p = subprocess.Popen(
        [ffprobe_path, "-i", "pipe:0", "-v", "quiet", "-print_format", "json", "-show_streams"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = json.loads(p.communicate(input=filestream.read())[0].decode("utf-8"))
    if data:
        raw_fps = data["streams"][0]["avg_frame_rate"].split("/")
        # if not int(raw_fps[0]) or not int(raw_fps[1]):
        #     raw_fps = data["streams"][0]["r_frame_rate"].split("/")
    else:
        raw_fps = [0, 0]
    if not int(raw_fps[0]) or not int(raw_fps[1]):
        # Can happen sometimes if the file isn't on the drive
        with open('tempfile', 'wb') as f:
            filestream.seek(0)
            f.write(filestream.read())
        p = subprocess.Popen(
            [ffprobe_path, "-i", "tempfile", "-v", "quiet", "-print_format", "json", "-show_streams"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        data = json.loads(p.communicate()[0].decode("utf-8"))
        raw_fps = data["streams"][0]["avg_frame_rate"].split("/")
        if not int(raw_fps[0]) or not int(raw_fps[1]):
            raw_fps = data["streams"][0]["r_frame_rate"].split("/")
        os.remove('tempfile')

    fps = int(raw_fps[0]) / int(raw_fps[1])
    return fps


def is_valid(file):
    file.seek(0)
    p = subprocess.Popen(
        ["ffprobe", "-i", "pipe:0", "-v", "quiet", "-print_format", "json", "-show_streams", "-count_frames"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = json.loads(p.communicate(input=file.read())[0].decode("utf-8"))
    if data:
        return data['streams'][0]['codec_type'] == "video"
    return False


def get_frames(file):
    file.seek(0)
    p = subprocess.Popen(
        ["ffprobe", "-i", "pipe:0", "-v", "quiet", "-print_format", "json", "-show_streams", "-count_frames"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = json.loads(p.communicate(input=file.read())[0].decode("utf-8"))
    if (not data or not (data.get('streams', [{}])[0].get('nb_read_frames', False) or data.get('streams', [{}])[0].get('nb_frames', False))) and isinstance(file, BytesIO):
        # Can happen sometimes if the file isn't on the drive
        with open('tempfile', 'wb') as f:
            file.seek(0)
            f.write(file.read())
        p = subprocess.Popen(
            ["ffprobe", "-i", "tempfile", "-v", "quiet", "-print_format", "json", "-show_streams", "-count_frames"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        data = json.loads(p.communicate()[0].decode("utf-8"))

    frames = int(data["streams"][0].get('nb_read_frames', 0))
    if not frames:
        frames = int(data['streams'][0].get('nb_read_frames', 0))

    return frames


def has_audio(file):
    file.seek(0)
    audio = False
    p = subprocess.Popen(
        ["ffprobe", "-i", "pipe:0", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = json.loads(p.communicate(input=file.read())[0].decode("utf-8"))
    for i in data['streams']:
        if i['codec_type'] == 'audio':
            audio = True

    return audio

import subprocess
import os
import json
import platform

if platform.system() == 'Windows':
    ffmpeg = 'ffmpeg.exe'
    ffprobe = 'ffprobe'
    gifski = 'gifski.exe'
else:
    ffmpeg = 'ffmpeg'
    ffprobe = 'ffprobe'
    gifski = 'gifski'

def concat(video, audio):
    """
    Combines video and audio
    :param video: video stream
    :param audio: audio stream
    :return:
    """

    print("Combining video and audio...")

    with open("video.mp4", "wb") as f:
        f.write(video.read())

    with open("audio.mp4", "wb") as f:
        f.write(audio.read())

    p = subprocess.Popen(
        [ffmpeg, "-loglevel", "panic", "-i", "video.mp4", "-i", "audio.mp4", "-c:v", "copy", "-c:a", "copy", "-y", "output.mp4"]
    )
    response = p.communicate()

    return open("output.mp4", "rb")
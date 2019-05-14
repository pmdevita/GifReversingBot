import subprocess
import os
import json
import platform
from io import BytesIO

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
        [ffmpeg, "-loglevel", "panic", "-i", "video.mp4", "-i", "audio.mp4", "-c:v", "copy", "-c:a", "copy", "-y",
         "temp.mp4"]
    )
    response = p.communicate()

    with open("temp.mp4", "rb") as f:
        file = BytesIO(f.read())
    return file

def vid_to_gif(image, path=False):
    """
    :param image: filestream to reverse
    :param path: if you just want the string path to the file instead of the filestream
    :return: filestream of a gif
    """
    if platform.system() == 'Windows':
        ffmpeg = '..\\ffmpeg.exe'
        ffprobe = '..\\ffprobe'
        gifski = '..\\gifski.exe'
    else:
        ffmpeg = 'ffmpeg'
        ffprobe = 'ffprobe'
        gifski = 'gifski'

    print("Reversing gif...")
    os.chdir("temp")

    with open("in.mp4", "wb") as f:
        f.write(image.read())

    # Get correct fps
    command = subprocess.Popen(
        [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", "in.mp4"],
        stdout=subprocess.PIPE)
    raw_fps = json.loads(command.communicate()[0].decode("utf-8"))["streams"][0]["r_frame_rate"].split("/")
    fps = int(raw_fps[0]) / int(raw_fps[1])
    print("FPS:", fps)

    print("Exporting frames...")

    p = subprocess.Popen(
        [ffmpeg, "-loglevel", "panic", "-i", "in.mp4", "frame%04d.png"]
    )
    response = p.communicate()

    if platform.system() == 'Windows':
        subprocess.Popen(
            ["del", "/Q", "in.mp4"],
            shell=True
        ).communicate()
    else:
        subprocess.Popen(
            ["rm in.mp4"],
            shell=True
        ).communicate()

    # Statistics
    for i in os.walk("."):
        files = i[2]
        break
    pics_size = sum(os.path.getsize(f) for f in files)
    print(pics_size)

    print("Rebuilding gif...")


    if platform.system() == 'Windows':
        p = subprocess.Popen(
            ['{}'.format(gifski), "-o", "../temp.gif", "--fps", str(round(fps)), "frame*.png"],
            shell=True
        )
    else:
        p = subprocess.Popen(
            ['{} -o ../temp.gif --fps {} frame*.png'.format(gifski, str(round(fps)))],
            shell=True
        )

    response = p.communicate()

    print("done")

    if platform.system() == 'Windows':
        subprocess.Popen(
            ["del", "/Q", "*"],
            shell=True
        ).communicate()
    else:
        subprocess.Popen(
            ["rm *"],
            shell=True
        ).communicate()


    os.chdir("..")

    # More statistics
    gif_size = os.path.getsize("temp.gif")
    print("pngs size, gif size, ratio", pics_size / 1000000, gif_size / 1000000, gif_size/pics_size)

    if path:
        return "temp.gif"
    else:
        return open("temp.gif", "rb")
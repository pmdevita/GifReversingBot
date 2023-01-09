import subprocess
import os
import json
import platform
from io import BytesIO
from gifreversingbot.utils.temp_folder import TempFolder

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

    with TempFolder("grbconcat") as temp_folder:
        with open(temp_folder / "video.mp4", "wb") as f:
            f.write(video.read())

        with open(temp_folder / "audio.mp4", "wb") as f:
            f.write(audio.read())

        subprocess.Popen(
            [ffmpeg, "-loglevel", "panic", "-i", temp_folder / "video.mp4", "-i", temp_folder / "audio.mp4",
             "-c:v", "copy", "-c:a", "copy", "-y", "temp.mp4"]
        ).communicate()

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
        ffmpeg = 'ffmpeg.exe'
        ffprobe = 'ffprobe'
        gifski = 'gifski.exe'
    else:
        ffmpeg = 'ffmpeg'
        ffprobe = 'ffprobe'
        gifski = 'gifski'

    print("Reversing gif...")
    with TempFolder("grb-vidgif") as temp_folder:

        with open(temp_folder / "in.mp4", "wb") as f:
            f.write(image.read())

        # Get correct fps
        command = subprocess.Popen(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",
             temp_folder / "in.mp4"],
            stdout=subprocess.PIPE)
        # TODO: Use the new metadata system
        raw_fps = json.loads(command.communicate()[0].decode("utf-8"))["streams"][0]["r_frame_rate"].split("/")
        fps = int(raw_fps[0]) / int(raw_fps[1])
        print("FPS:", fps)

        print("Exporting frames...")

        subprocess.Popen(
            [ffmpeg, "-loglevel", "panic", "-i", "in.mp4", "frame%04d.png"]
        ).communicate()

        os.remove(temp_folder / "in.mp4")

        # Statistics
        for i in os.walk(temp_folder):
            files = i[2]
            break
        pics_size = sum(os.path.getsize(temp_folder / f) for f in files)
        print(pics_size)

        print("Rebuilding gif...")

        if platform.system() == 'Windows':
            p = subprocess.Popen(
                ['{}'.format(gifski), "-o", "../temp.gif", "--fps", str(round(fps)), temp_folder / "frame*.png"],
                shell=True
            )
        else:
            p = subprocess.Popen(
                [f"{gifski} -o ../temp.gif --fps {str(round(fps))} {temp_folder / 'frame*.png'}"],
                shell=True
            )

        p.communicate()

    print("done")

    # More statistics
    gif_size = os.path.getsize("temp.gif")
    print("pngs size, gif size, ratio", pics_size / 1000000, gif_size / 1000000, gif_size / pics_size)

    if path:
        return "temp.gif"
    else:
        return open("temp.gif", "rb")

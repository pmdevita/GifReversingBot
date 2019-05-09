import subprocess
import os
import json
import platform
from core import constants as consts
from core.file import get_fps

def zeros(number, num_zeros=6):
    string = str(number)
    return "".join(["0" for i in range(num_zeros - len(string))]) + string

def reverse_gif(image, path=False, format=consts.GIF):
    """
    :param image: filestream to reverse
    :param path: if you just want the string path to the file instead of the filestream
    :return: filestream of a gif
    """
    image.seek(0)
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

    filename = "in." + format

    with open(filename, "wb") as f:
        f.write(image.read())

    # Get correct fps
    # with open(filename, "rb") as f:
    #     fps = get_fps(f)
    # Gross hack, fix it later with integrated GifFile metadata
    if platform.system() == 'Windows':
        fps = get_fps(image, "../ffprobe")
    else:
        fps = get_fps(image)
    print("FPS:", fps)

    print("Exporting frames...")

    # Reverse filenames
    p = subprocess.Popen(
        [ffmpeg, "-loglevel", "quiet", "-i", filename, "original%06d.png"]
    )
    # Reverse frame order in export
    # p = subprocess.Popen(
    #     [ffmpeg, "-loglevel", "info", "-i", "-vf", "reverse", filename, "frame%06d.png"]
    # )
    response = p.communicate()


    if platform.system() == 'Windows':
        subprocess.Popen(
            ["del", "/Q", filename],
            shell=True
        ).communicate()
    else:
        subprocess.Popen(
            ["rm {}".format(filename)],
            shell=True
        ).communicate()


    # Reverse filenames
    for i in os.walk("."):
        files = i[2]
        break

    counter = len(files)
    for i in range(1, len(files) + 1):
        os.rename("original{}.png".format(zeros(i)), "frame{}.png".format(zeros(counter)))
        counter -= 1

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

def reverse_mp4(mp4, audio=False, format=consts.MP4, output=consts.MP4):
    """
    :param mp4: filestream to reverse (must be a mp4)
    :return: filestream of an mp4
    """
    print("Reversing {} into {}...".format(format, output))

    loglevel = "error"

    mp4.seek(0)
    if output == consts.MP4:
        in_file = "source.mp4"
        out_file = "temp.mp4"
        mute = ["ffmpeg", "-loglevel", loglevel, "-i", "pipe:0", "-vf", "reverse", "-c:v", "libx264",
                "-q:v", "0", "-y", "-f", "mp4", "temp.mp4"]
        sound = ["ffmpeg", "-loglevel", loglevel, "-i", "pipe:0", "-vf", "reverse", "-af", "areverse", "-c:v", "libx264",
                 "-q:v", "0", "-y", "-f", "mp4", "temp.mp4"]
    elif output == consts.WEBM:
        in_file = "source.webm"
        out_file = "temp.webm"
        mute = ["ffmpeg", "-loglevel", loglevel, "-i", "pipe:0", "-vf", "reverse", "-c:v", "libvpx",
                "-q:v", "0", "-y", "-f", "webm", "temp.webm"]
        sound = ["ffmpeg", "-loglevel", loglevel, "-i", "pipe:0", "-vf", "reverse", "-af", "areverse", "-c:v", "libvpx",
                 "-q:v", "0", "-y", "-f", "webm", "temp.webm"]

    if audio:
        command = sound
    else:
        command = mute

    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    response = p.communicate(input=mp4.read())[0].decode()

    print(response)

    # Weird thing
    if "partial file" in response:
        print("FFMPEG gave weird error, putting in file to reverse")
        command[4] = in_file
        mp4.seek(0)
        with open(in_file, 'wb') as f:
            f.write(mp4.read())

        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = p.communicate()[0].decode()
        os.remove(in_file)

    reversed = open(out_file, "rb")

    return reversed
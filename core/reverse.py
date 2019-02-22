import subprocess
import os
import json
import platform


def old_reversegif(image, path=False):
    """
    :param image: filestream to reverse (must be a gif)
    :param path: if you just want the string path to the file instead of the filestream
    :return: filestream of a gif
    """
    print("Reversing gif...")
    # Setup ImageMagick limits so we don't die
    #os.environ['MAGICK_MEMORY_LIMIT'] = "1GB"
    #os.environ['MAGICK_MAP_LIMIT'] = "1GB"
    #os.environ['MAGICK_AREA_LIMIT'] = "1GB"

    p = subprocess.Popen(
        ["convert", "-", "-coalesce", "-reverse", "-verbose", "-layers", "OptimizePlus", "-loop", "0", "temp.gif"],
        stdin=subprocess.PIPE)
    response = p.communicate(input=image.read())
    print(response)
    if path:
        return "temp.gif"
    else:
        return open("temp.gif", "rb")

def reverse_gif(image, path=False):
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
        [ffmpeg, "-loglevel", "panic", "-i", "in.mp4", "-vf", "reverse", "frame%04d.png"]
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

def reverse_mp4(mp4, audio=False):
    """
    :param mp4: filestream to reverse (must be a mp4)
    :return: filestream of an mp4
    """
    print("Reversing mp4...")

    mute = ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-vf", "reverse", "-c:v", "libx264",
            "-q:v", "0", "-y", "-f", "mp4", "temp.mp4"]
    sound = ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-vf", "reverse", "-af", "areverse", "-c:v", "libx264",
             "-q:v", "0", "-y", "-f", "mp4", "temp.mp4"]

    if audio:
        command = sound
    else:
        command = mute

    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    response = p.communicate(input=mp4.read())[0].decode()

    # Weird thing
    if "partial file" in response:
        print("FFMPEG gave weird error, putting in file to reverse")
        command[4] = "source.mp4"
        mp4.seek(0)
        with open("source.mp4", 'wb') as f:
            f.write(mp4.read())

        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = p.communicate()[0].decode()
        os.remove("source.mp4")

    reversed = open("temp.mp4", "rb")

    return reversed
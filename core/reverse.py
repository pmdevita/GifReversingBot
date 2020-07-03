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
            ['{}'.format(gifski), "-o", "../temp.gif", "--fps", str(max(round(fps), 1)), "frame*.png"],
            shell=True
        )
    else:
        p = subprocess.Popen(
            ['{} -o ../temp.gif --fps {} frame*.png'.format(gifski, str(max(round(fps), 1)))],
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

    mp4.seek(0)

    # Create the params for the command

    params = {"loglevel": "info", "audio": ""}

    if output == consts.MP4:
        params['codec'] = "-c:v libx264 -q:v 0"
    elif output == consts.WEBM:
        params['codec'] = "-c:v libvpx -crf 8 -b:v 1500K"

    if audio:
        params['audio'] = "-af areverse "

    # Assemble command

    command = "ffmpeg -loglevel {loglevel} -i pipe:0 -vf reverse {codec} {audio}-y temp.{output}".format(output=output,
                                                                                                         **params)

    # command = "ffmpeg -loglevel {loglevel} -i pipe:0 -y temp.{output}".format(output=output, **params)

    print(command)
    command = command.split()

    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    response = p.communicate(input=mp4.read())

    print(response[0].decode() if response[0] else None, response[1].decode() if response[1] else None)

    response = response[0].decode()
    print(os.path.getsize('temp.' + output))
    # Weird thing
    # A blank mp4 is 48 bytes, a blank webm is ~~632 bytes~~
    # Blank webm might be larger actually, using a percentage of the size of the original
    if output == consts.WEBM:
        print("Checking if under", mp4.getbuffer().nbytes / 100)
    if "partial file" in response or "Cannot allocate memory" in response or os.path.getsize('temp.' + output) <= (48 if output == consts.MP4 else (mp4.getbuffer().nbytes / 100)):
        """"frame=    0 fps=0.0 q=0.0 size=       1kB time=00:00:00.00 bitrate=N/A"""
        """"frame=    0 fps=0.0 q=0.0 size=       0kB time=00:00:00.00"""
        print("FFMPEG gave weird error, putting in file to reverse")
        in_file = "source." + format
        command[4] = in_file
        mp4.seek(0)
        with open(in_file, 'wb') as f:
            f.write(mp4.read())

        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = p.communicate()[0].decode()

        print(response)
        # Did we fail again?
        # if "partial file" in response or "Cannot allocate memory" in response or os.path.getsize('temp.' + output) <= (48 if output == consts.MP4 else 632):
        #     # Just export frames and reconstruct
        #     print("Exporting frames")
        #     # Get FPS
        #     # Gross hack, fix it later with integrated GifFile metadata
        #     fps = get_fps(in_file)
        #
        #     os.chdir("temp")
        #
        #     # Export frames
        #     p = subprocess.Popen(
        #         [ffmpeg, "-loglevel", "quiet", "-i", "../" + in_file, "original%06d.png"]
        #     )
        #
        #     response = p.communicate()
        #
        #     print("Renaming...")
        #     # Reverse filenames
        #     for i in os.walk("."):
        #         files = i[2]
        #         break
        #
        #     counter = len(files)
        #     for i in range(1, len(files) + 1):
        #         os.rename("original{}.png".format(zeros(i)), "frame{}.png".format(zeros(counter)))
        #         counter -= 1
        #
        #     # Statistics
        #     for i in os.walk("."):
        #         files = i[2]
        #         break

        os.remove(in_file)

    reversed_file = open("temp." + output, "rb")

    return reversed_file



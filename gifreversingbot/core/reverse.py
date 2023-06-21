import subprocess
import os
import platform
from pathlib import Path

from gifreversingbot.core import constants as consts
from gifreversingbot.hosts import GifFile
from gifreversingbot.utils.temp_folder import TempFolder


def zeros(number, num_zeros=6):
    string = str(number)
    return "".join(["0" for i in range(num_zeros - len(string))]) + string


def reverse_gif(image_file: GifFile, folder: Path, path=False, format=consts.GIF):
    """
    :param image: filestream to reverse
    :param path: if you just want the string path to the file instead of the filestream
    :return: filestream of a gif
    """
    image = image_file.file
    image.seek(0)
    if platform.system() == 'Windows':
        ffmpeg = 'ffmpeg.exe'
        ffprobe = 'ffprobe'
        gifski = 'gifski.exe'
    else:
        ffmpeg = 'ffmpeg'
        ffprobe = 'ffprobe'
        gifski = 'gifski'

    print("Reversing gif...")

    frames_folder = folder / "frames"
    frames_folder.mkdir()

    filename = folder / ("in." + format)

    with open(filename, "wb") as f:
        f.write(image.read())

    fps = image_file.info.fps
    print("FPS:", fps)

    print("Exporting frames...")

    # Reverse filenames
    subprocess.Popen(
        [ffmpeg, "-loglevel", "quiet", "-i", str(filename), "-vsync", "0", frames_folder / "original%06d.png"]
    ).communicate()

    os.remove(filename)

    # Reverse filenames
    for i in os.walk(frames_folder):
        files = i[2]
        break

    counter = len(files)
    for i in range(1, len(files) + 1):
        os.rename(frames_folder / "original{}.png".format(zeros(i)),
                  frames_folder / "frame{}.png".format(zeros(counter)))
        counter -= 1

    # Statistics
    for i in os.walk(frames_folder):
        files = i[2]
        break

    pics_size = sum(os.path.getsize(frames_folder / f) for f in files)
    print(pics_size)

    print("Rebuilding gif...")

    if platform.system() == 'Windows':
        p = subprocess.Popen(
            [gifski, "-o", str(folder / "temp.gif"), "--fps", str(max(round(fps), 1)), str(frames_folder / "frame*.png")],
            shell=True,
            stderr=subprocess.PIPE
        )
    else:
        p = subprocess.Popen(
            [f"{gifski} -o {folder / 'temp.gif'} --fps {str(max(round(fps), 1))} {frames_folder / 'frame*.png'}"],
            shell=True,
            stderr=subprocess.PIPE
        )

    output = p.communicate()

    print(output)

    print("done")

    # More statistics
    gif_size = os.path.getsize(folder / "temp.gif")
    print("pngs size, gif size, ratio", pics_size / 1000000, gif_size / 1000000, gif_size / pics_size)

    if path:
        return "temp.gif"
    else:
        return open(folder / "temp.gif", "rb")


def reverse_mp4(mp4, folder: Path, audio=False, format=consts.MP4, output=consts.MP4):
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

    params['output_file'] = folder / f"temp.{output}"

    # Assemble command
    command = "ffmpeg -loglevel {loglevel} -i pipe:0 -vf reverse {codec} {audio}-y {output_file}".format(output=output,
                                                                                                         **params)

    # command = "ffmpeg -loglevel {loglevel} -i pipe:0 -y temp.{output}".format(output=output, **params)

    # print(command)
    command = command.split()

    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    response = p.communicate(input=mp4.read())

    # print(response[0].decode() if response[0] else None, response[1].decode() if response[1] else None)

    response = response[0].decode()
    # print(os.path.getsize('temp.' + output))

    # Weird thing
    # A blank mp4 is 48 bytes, a blank webm is ~~632 bytes~~
    # Blank webm might be larger actually, using a percentage of the size of the original
    # if output == consts.WEBM:
    #     print("Checking if under", mp4.getbuffer().nbytes / 100)
    if "partial file" in response or "Cannot allocate memory" in response or \
            os.path.getsize(params['output_file']) <= (48 if output == consts.MP4 else (mp4.getbuffer().nbytes / 100)):
        """"frame=    0 fps=0.0 q=0.0 size=       1kB time=00:00:00.00 bitrate=N/A"""
        """"frame=    0 fps=0.0 q=0.0 size=       0kB time=00:00:00.00"""
        print("FFMPEG gave weird error, putting in file to reverse")
        in_file = folder / ("source." + format)
        command[4] = in_file
        mp4.seek(0)
        with open(in_file, 'wb') as f:
            f.write(mp4.read())

        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = p.communicate()[0].decode()

        # print(response)
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

    if os.path.getsize(params['output_file']) <= (48 if output == consts.MP4 else 632):
        return [os.path.getsize(params['output_file']), output]
    else:
        return open(params['output_file'], "rb")

import os
import pathlib
import platform
import shutil
from pathlib import Path
from ..core import constants as consts


class _OSTempLocation:
    _temp_location = None

    @classmethod
    def temp_location(cls):
        if not cls._temp_location:
            cls._temp_location = cls._get_temp_location()
        return cls._temp_location

    @classmethod
    def _get_temp_location(cls) -> Path:
        system = platform.system()
        if system == "Windows":
            return Path(os.environ["TEMP"])
        if system == "Linux":
            if os.environ.get("TMPDIR", None):
                return Path(os.environ["TMPDIR"])
            return Path("/tmp")


class TempFolder:
    def __init__(self, name=None):
        if name is None:
            name = consts.bot_name + "temp"
        self.name = name
        self.folder = _OSTempLocation.temp_location() / self.name
        if self.folder.exists():
            print("Deleting existing temp folder...")
            shutil.rmtree(self.folder)
        os.mkdir(self.folder)

    def __enter__(self) -> Path:
        return self.folder

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        shutil.rmtree(self.folder)

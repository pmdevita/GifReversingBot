import configparser
import os
dirname = os.path.dirname(__file__)
default_path = os.path.join(dirname, '../credentials.ini')

class CredentialsLoader:
    config = None
    path = default_path

    @classmethod
    def get_credentials(cls, file=None):
        if not cls.config:
            if file:
                cls.path = file

            cls.config = configparser.ConfigParser()
            cls.config.read(cls.path)

            if len(cls.config.sections()) < 1:
                raise Exception("config file is wrong")
        return cls.config

    @classmethod
    def set_credential(cls, section, name, value):
        cls.config.set(section, name, value)
        with open(cls.path, "w") as f:
            cls.config.write(f)

import configparser

class CredentialsLoader:
    config = None

    @classmethod
    def get_credentials(cls, file=None):
        if not cls.config:
            path = "credentials.ini"
            if file:
                path = file

            cls.config = configparser.ConfigParser()
            cls.config.read(path)

            if len(cls.config.sections()) < 1:
                raise Exception("config file is wrong")
        return cls.config
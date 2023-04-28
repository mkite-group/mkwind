import os


class TemporaryChdir:
    def __init__(self, to: os.PathLike):
        self.workdir = to
        self.basedir = os.getcwd()

    def __enter__(self):
        os.chdir(self.workdir)

    def __exit__(self, exc_type, exc_value, tb):
        os.chdir(self.basedir)

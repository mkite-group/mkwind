import os
from enum import IntEnum
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggerLevel(IntEnum):
    ERROR = 4
    WARNING = 3
    INFO = 2
    DEBUG = 1


class LoggerHook(ABC):
    @abstractmethod
    def log(self, msg: str, format: bool = True):
        pass

    def format(self, msg: str, level: LoggerLevel = LoggerLevel.INFO):
        return f"{self.get_timestamp()} {self.get_level(level):8}: {msg}"

    def get_timestamp(self, fmt=TIME_FORMAT):
        return datetime.now().strftime(fmt)

    def get_level(self, priority: LoggerLevel = LoggerLevel.INFO):
        return priority.name


class PrintHook(LoggerHook):
    def log(self, msg: str, format: bool = True):
        if format:
            msg = self.format(msg)

        print(msg)


class FileHook(LoggerHook):
    def __init__(self, filepath: os.PathLike, clean: bool = False):
        self.setup(filepath, clean=clean)
        self.filepath = filepath

    def setup(self, filepath: os.PathLike, clean: bool = False):
        if clean and os.path.exists(filepath):
            os.remove(filepath)

    def log(self, msg: str, format: bool = True):
        if not msg.endswith("\n"):
            msg += "\n"

        if format:
            msg = self.format(msg)

        with open(self.filepath, "a+") as f:
            f.write(msg)


class Logger:
    def __init__(self, hooks: List[LoggerHook]):
        self.hooks = hooks

    def log(self, msg: str, format: bool = True):
        for h in self.hooks:
            h.log(msg, format=format)

    def newline(self):
        for h in self.hooks:
            h.log("\n", format=False)

    def hbar(self, length=29):
        for h in self.hooks:
            h.log("=" * length, format=False)

    @classmethod
    def to_file(cls, filepath: os.PathLike, stdout: bool = False):
        hooks = [FileHook(filepath)]
        if stdout:
            hooks += [PrintHook()]

        return cls(hooks)

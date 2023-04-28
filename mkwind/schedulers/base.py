import subprocess
from typing import Union
from pydantic import BaseModel
from abc import ABC, abstractmethod

from mkwind.user import EnvSettings
from mkwind.templates import Template


class SchedulerJob(BaseModel):
    id: int
    name: str
    start_time: Union[str, None]
    partition: str = ""
    group: str
    status: str


class SchedulerError(Exception):
    pass


class Scheduler(ABC):
    TEMPLATE: Template = None
    SUBMIT_CMD: str = None
    STATUS_CMD: str = None

    def __init__(self, settings: EnvSettings):
        self.settings = settings

    def _run(self, cmd) -> str:
        try:
            out = subprocess.check_output(cmd, shell=True).decode()
            return out
        except subprocess.CalledProcessError as e:
            raise SchedulerError(str(e))

    @abstractmethod
    def submit_job(self, job):
        pass

    @abstractmethod
    def get_all(self, job) -> SchedulerJob:
        pass

    @abstractmethod
    def get_queued(self) -> SchedulerJob:
        pass

    @abstractmethod
    def get_pending(self) -> SchedulerJob:
        pass

    @abstractmethod
    def get_running(self) -> SchedulerJob:
        pass

    @abstractmethod
    def get_done(self) -> SchedulerJob:
        pass

    @abstractmethod
    def get_error(self) -> SchedulerJob:
        pass

    @abstractmethod
    def get_failed(self) -> SchedulerJob:
        pass

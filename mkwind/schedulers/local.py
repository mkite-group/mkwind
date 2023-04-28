import os
from typing import List

from mkwind.jobs.dirmanager import TemporaryChdir
from mkwind.templates import Template

from .base import Scheduler, SchedulerJob


LOCAL_JOB_IDENTIFIER = "LocalJob_mkwind"

class LocalScheduler(Scheduler):
    TEMPLATE = Template.from_name("slurm.sh")
    SUBMIT_CMD = f"exec -a {LOCAL_JOB_IDENTIFIER} bash"
    STATUS_CMD = f"ps aux | grep \"exec -a {LOCAL_JOB_IDENTIFIER}\" | grep -v grep | awk '{print $2}'"

    def submit_job(self, job_folder: os.PathLike):
        name = os.path.basename(job_folder)
        with TemporaryChdir(to=job_folder):
            cmd = f"bash -c \"{self.SUBMIT_CMD} {self.TEMPLATE.FILENAME}\""
            out = self._run(cmd)

        return out

    def get_all(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD}"
        return self._run(cmd)

    def get_queued(self) -> List[SchedulerJob]:
        return []

    def get_pending(self) -> List[SchedulerJob]:
        return []

    def get_running(self) -> List[SchedulerJob]:
        return self.get_all()

    def get_done(self) -> List[SchedulerJob]:
        return []

    def get_error(self) -> List[SchedulerJob]:
        return []

    def get_failed(self) -> List[SchedulerJob]:
        return []


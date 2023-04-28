import os
from enum import Enum
from typing import List

from mkwind.jobs.dirmanager import TemporaryChdir
from mkwind.templates import Template

from .base import Scheduler, SchedulerJob


class SlurmFormats(Enum):
    USER = "%u"
    JOBID = "%i"
    JOBNAME = "%j"
    STARTTIME = "%S"
    PARTITION = "%P"
    QOS = "%q"
    STATE = "%T"


class SlurmScheduler(Scheduler):
    TEMPLATE = Template.from_name("slurm.sh")
    SUBMIT_CMD = "sbatch"
    STATUS_CMD = 'squeue -h --format="%i %j %S %P %q %T"'
    STATUS_HEADER = [
        "id",
        "name",
        "start_time",
        "partition",
        "group",
        "status",
    ]

    def submit_job(self, job_folder: os.PathLike):
        name = os.path.basename(job_folder)
        with TemporaryChdir(to=job_folder):
            cmd = f"{self.SUBMIT_CMD} --job-name={name} {self.TEMPLATE.FILENAME}"
            out = self._run(cmd)

        return out

    @property
    def user_filter(self):
        return f"-u {self.settings.USER}"

    def get_all(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter}"
        out = self._run(cmd)
        return self.format_output(out)

    def get_queued(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t CONFIGURING,COMPLETING,PENDING,RUNNING,RESIZING,SUSPENDED"
        out = self._run(cmd)
        return self.format_output(out)

    def get_pending(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t PENDING"
        out = self._run(cmd)
        return self.format_output(out)

    def get_running(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t RUNNING"
        out = self._run(cmd)
        return self.format_output(out)

    def get_done(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t COMPLETED"
        out = self._run(cmd)
        return self.format_output(out)

    def get_error(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t CANCELLED,FAILED,TIMEOUT"
        out = self._run(cmd)
        return self.format_output(out)

    def get_failed(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -t PREEMPTED,NODE_FAIL"
        out = self._run(cmd)
        return self.format_output(out)

    def format_output(self, out) -> List[SchedulerJob]:
        out = out.strip()
        if not out:
            return []

        lines = out.split("\n")
        jobs = []
        for jobline in lines:
            jobdict = dict(zip(self.STATUS_HEADER, jobline.split(" ")))
            jobs.append(SchedulerJob(**jobdict))

        return jobs

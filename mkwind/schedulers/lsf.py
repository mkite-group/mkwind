import os
import json
from enum import Enum
from typing import List

from mkwind.jobs.dirmanager import TemporaryChdir
from mkwind.templates import Template

from .base import Scheduler, SchedulerJob


class LsfScheduler(Scheduler):
    TEMPLATE = Template.from_name("lsf.sh")
    SUBMIT_CMD = "bsub"
    STATUS_CMD = 'bquery -o "JOBID QUEUE STAT JOB_GROUP START_TIME JOB_NAME" -json'
    STATUS_HEADER = [
        "id",
        "partition",
        "status",
        "group",
        "start_time",
        "name",
    ]

    def submit_job(self, job_folder: os.PathLike):
        name = os.path.basename(job_folder)
        with TemporaryChdir(to=job_folder):
            cmd = f"{self.SUBMIT_CMD} -J {name} < {self.TEMPLATE.FILENAME}"
            out = self._run(cmd)

        return out

    @property
    def user_filter(self):
        return f"-u {self.settings.USER}"

    def format_output(self, out) -> List[SchedulerJob]:
        out = out.strip()
        if not out:
            return []

        response = json.loads(out)
        if "RECORDS" not in response:
            return []

        jobstatus = response["RECORDS"]
        jobs = []
        for stat in jobstatus:
            jobdict = dict(zip(self.STATUS_HEADER, stat.values()))
            jobs.append(SchedulerJob(**jobdict))

        return jobs

    def get_all(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter}"
        out = self._run(cmd)
        return self.format_output(out)

    def get_by_status(self, status_list: List[str]) -> List[SchedulerJob]:
        jobs = self.get_all()
        return [
            j for j in jobs
            if j.status in status_list
        ]

    def get_queued(self) -> List[SchedulerJob]:
        return self.get_by_status(["RUN", "PEND", "PSUSP"])

    def get_pending(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -p"
        out = self._run(cmd)
        return self.format_output(out)

    def get_running(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -r"
        out = self._run(cmd)
        return self.format_output(out)

    def get_done(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -d"
        out = self._run(cmd)
        return self.format_output(out)

    def get_error(self) -> List[SchedulerJob]:
        return self.get_by_status(["EXIT"])

    def get_failed(self) -> List[SchedulerJob]:
        return self.get_error()


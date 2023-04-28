import os
import msgspec as msg
from typing import List, Union, Dict, BinaryIO

from mkwind.jobs.dirmanager import TemporaryChdir
from mkwind.templates import Template

from .base import Scheduler, SchedulerJob


class PueueTaskStatus(msg.Struct):
    id: int
    label: str
    start: Union[str, None]
    group: str
    status: Union[str, dict]


class PueueTask(msg.Struct):
    task: PueueTaskStatus
    output: str


class PueueScheduler(Scheduler):
    TEMPLATE = Template.from_name("slurm.sh")
    SUBMIT_CMD = f"pueue add"
    STATUS_CMD = f"pueue log --json"

    def submit_job(self, job_folder: os.PathLike):
        name = os.path.basename(job_folder)
        with TemporaryChdir(to=job_folder):
            cmd = f"chmod +x ./{self.TEMPLATE.FILENAME}"
            out = self._run(cmd)

            cmd = f"{self.SUBMIT_CMD} -l {name} ./{self.TEMPLATE.FILENAME}"
            out = self._run(cmd)

        return out

    def format_output(self, tasks: Dict[str, PueueTask]):
        schedjobs = []
        for item in tasks.values():
            t = item.task
            if isinstance(t.status, dict):
                status = t.status.get("Done", "Failed")
                if isinstance(status, dict):
                    status = list(status.keys())[0]
            elif isinstance(t.status, str):
                status = t.status

            sjob = SchedulerJob(
                id=t.id,
                name=t.label,
                start_time=t.start,
                group=t.group,
                status=status,
            )

            schedjobs.append(sjob)

        return schedjobs

    @property
    def status(self) -> dict:
        cmd = f"{self.STATUS_CMD}"
        out = self._run(cmd)
        return self.decode_status(out.encode())

    def decode_status(self, out: BinaryIO):
        decoder = msg.json.Decoder(Dict[str, PueueTask])
        return decoder.decode(out)

    def get_all(self) -> List[SchedulerJob]:
        return self.format_output(self.status)

    def get_filtered_by_status(self, status: str) -> List[SchedulerJob]:
        jobs = self.get_all()
        return [j for j in jobs if j.status == status]

    def get_queued(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Queued")

    def get_pending(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Queued")

    def get_running(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Running")

    def get_done(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Success")

    def get_error(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Error")

    def get_failed(self) -> List[SchedulerJob]:
        return self.get_filtered_by_status("Error")

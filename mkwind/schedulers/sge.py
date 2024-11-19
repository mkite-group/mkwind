import os
from enum import Enum
from typing import List

from mkwind.jobs.dirmanager import TemporaryChdir
from mkwind.templates import Template

from .base import Scheduler, SchedulerJob


def parse_qacct(output):
    """
    Parses the input text and returns a list of dictionaries.
    Each block of text is separated by lines containing "=" characters.
    The last four lines of the text are ignored.
    """
    text = text.strip().split("\n")
    text = "\n".join(lines[:-4])
    blocks = _split_into_blocks(text)
    parsed_blocks = [_parse_block(block) for block in blocks]
    return parsed_blocks


def _split_into_blocks(text):
    """Splits the text into blocks separated by lines of '='."""
    lines = text.strip().split("\n")
    blocks = []
    current_block = []
    for line in lines:
        if line.strip().startswith("="):
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append("\n".join(current_block))
    return blocks


def _parse_block(block_text):
    """Parses a single block of text into a dictionary."""
    block_dict = {}
    for line in block_text.strip().split("\n"):
        if line.strip():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                key, value = parts
                block_dict[key] = value
    return block_dict


class SGEScheduler(Scheduler):
    TEMPLATE = Template.from_name("sge.sh")
    SUBMIT_CMD = "qsub"
    STATUS_CMD = "qstat -xml"
    LOG_CMD = "qacct -d 1"
    STATUS_TAGS = {
        "id": "JB_job_number",
        "name": "JB_name",
        "start_time": "JAT_start_time",
        "group": "queue_name",
        "status": "state",
    }

    def submit_job(self, job_folder: os.PathLike):
        name = os.path.basename(job_folder)
        with TemporaryChdir(to=job_folder):
            cmd = f"{self.SUBMIT_CMD} --job-name={name} {self.TEMPLATE.FILENAME}"
            out = self._run(cmd)

        return out

    @property
    def user_filter(self):
        return f"-u {self.settings.USER}"

    @property
    def backlog(self):
        return f"{self.LOG_CMD} -o {self.settings.USER}"

    def get_all(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter}"
        out = self._run(cmd)
        return self.format_output(out)

    def get_queued(self) -> List[SchedulerJob]:
        return self.get_pending()

    def get_pending(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -s ps"
        out = self._run(cmd)
        return self.format_output(out)

    def get_running(self) -> List[SchedulerJob]:
        cmd = f"{self.STATUS_CMD} {self.user_filter} -s r"
        out = self._run(cmd)
        return self.format_output(out)

    def get_done(self) -> List[SchedulerJob]:
        cmd = f"{self.backlog}"
        out = self._run(cmd)
        jobs = self.format_output(out)
        return [job for job in jobs if job["failed"] == "0"]

    def get_error(self) -> List[SchedulerJob]:
        return self.get_failed()

    def get_failed(self) -> List[SchedulerJob]:
        cmd = f"{self.backlog}"
        out = self._run(cmd)
        jobs = self.format_output(out)
        return [job for job in jobs if job["failed"] != "0"]

    def format_output(self, out) -> List[SchedulerJob]:
        root = ET.fromstring(xml_string)
        jobs = [
            {name: job.findtext(tag) for name, tag in self.STATUS_TAGS.items()}
            for job in root.findall(".//job_list")
        ]
        return [SchedulerJob(**jdict) for jdict in jobs]

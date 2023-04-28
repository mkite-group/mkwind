import os
import re
from typing import List
from pathlib import Path
import unittest as ut
from unittest.mock import patch
from pkg_resources import resource_filename

from mkwind.user import EnvSettings
from mkwind.schedulers.base import SchedulerJob
from mkwind.schedulers.slurm import SlurmScheduler
from mkite_core.tests.tempdirs import run_in_tempdir


SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")

STATUS = """
1010202 job.sh 2022-07-26T00:01:02 pbatch normal COMPLETED
1010203 job.sh 2022-07-26T00:01:02 pbatch normal COMPLETED
1010204 job.sh 2022-07-26T00:01:02 pbatch normal TIMEOUT
1010205 job.sh 2022-07-26T00:01:02 pbatch normal RUNNING
1010206 job.sh 2022-07-26T00:01:02 pbatch normal RUNNING
1010207 job.sh 2022-07-26T00:01:02 pbatch normal RUNNING
1010207 job.sh 2022-07-26T00:01:02 pbatch normal NODE_FAIL
1010208 job.sh N/A pdebug normal PENDING
1010209 job.sh N/A pdebug normal PENDING
1010210 job.sh N/A pdebug normal PENDING
1010211 job.sh N/A pdebug normal PENDING
"""


class MockSlurmScheduler(SlurmScheduler):
    SUBMIT_CMD = "echo"

    def _run(self, cmd):
        if self.STATUS_CMD in cmd:
            return self._run_status(cmd)

        if self.SUBMIT_CMD in cmd:
            return super()._run(cmd)

        raise ValueError(f"command {cmd} does not have the expected format")

    def _run_status(self, cmd):
        tags = re.findall(".*-t\s([A-Z,]+)", cmd)

        if len(tags) == 0:
            return STATUS

        tags = tags[0].split(",")
        return self._filtered_status(tags)

    def _filtered_status(self, tags: List[str]):
        filtered = []
        for line in STATUS.split("\n"):
            if any([t in line for t in tags]):
                filtered.append(line)

        return "\n".join(filtered)


class TestSlurmScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockSlurmScheduler(settings=settings)

    @run_in_tempdir
    def test_submit(self):
        NAME = "testname"
        os.mkdir(NAME)
        Path(f"{NAME}/job.sh").touch()

        out = self.sched.submit_job(NAME)
        expected = f"--job-name={NAME} job.sh\n"

        self.assertEqual(out, expected)

    def test_format(self):
        out = "\n".join(STATUS.strip().split("\n")[:2])
        sjobs = self.sched.format_output(out)

        self.assertEqual(len(sjobs), 2)
        self.assertIsInstance(sjobs, list)
        self.assertIsInstance(sjobs[0], SchedulerJob)

    def test_status(self):
        sjobs = self.sched.get_all()
        nlines = len(STATUS.strip().split("\n"))

        self.assertEqual(len(sjobs), nlines)

    def test_running(self):
        sjobs = self.sched.get_running()
        self.assertEqual(len(sjobs), 3)

    def test_failed(self):
        sjobs = self.sched.get_failed()
        self.assertEqual(len(sjobs), 1)

    def test_error(self):
        sjobs = self.sched.get_error()
        self.assertEqual(len(sjobs), 1)

    def test_done(self):
        sjobs = self.sched.get_done()
        self.assertEqual(len(sjobs), 2)

    def test_pending(self):
        sjobs = self.sched.get_pending()
        self.assertEqual(len(sjobs), 4)

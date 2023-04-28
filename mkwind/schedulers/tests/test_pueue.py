import os
from pathlib import Path
from pkg_resources import resource_filename

import unittest as ut
from unittest.mock import patch

from mkwind.user import EnvSettings
from mkwind.schedulers.base import SchedulerJob
from mkwind.schedulers.pueue import PueueScheduler, PueueTask, PueueTaskStatus
from mkite_core.tests.tempdirs import run_in_tempdir


SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
STATUS_FILE = resource_filename("mkwind.schedulers.tests.files", "pueue.json")


class MockPueueScheduler(PueueScheduler):
    SUBMIT_CMD = "echo"

    @property
    def status(self):
        with open(STATUS_FILE, "rb") as f:
            out = f.read()

        return self.decode_status(out)


class TestPueueScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockPueueScheduler(settings=settings)

    @run_in_tempdir
    def test_submit(self):
        NAME = "testname"
        os.mkdir(NAME)
        Path(f"{NAME}/job.sh").touch()

        out = self.sched.submit_job(NAME)
        expected = f"-l {NAME} ./job.sh\n"

        self.assertEqual(out, expected)

    def test_status(self):
        jobs = self.sched.status
        self.assertIsInstance(jobs, dict)

        k = list(jobs.keys())[0]
        self.assertIsInstance(jobs[k], PueueTask)

    def test_get_and_format(self):
        jobs = self.sched.get_all()
        self.assertIsInstance(jobs, list)
        self.assertEqual(len(jobs), 3)
        self.assertIsInstance(jobs[0], SchedulerJob)

    def test_filter(self):
        jobs = self.sched.get_filtered_by_status("Success")
        self.assertEqual(len(jobs), 1)

    def test_gets(self):
        self.assertEqual(len(self.sched.get_queued()), 1)
        self.assertEqual(len(self.sched.get_running()), 1)
        self.assertEqual(len(self.sched.get_pending()), 1)
        self.assertEqual(len(self.sched.get_done()), 1)
        self.assertEqual(len(self.sched.get_error()), 0)

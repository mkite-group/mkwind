import os
from pathlib import Path
from pkg_resources import resource_filename

import unittest as ut
from unittest.mock import patch

from mkwind.user import EnvSettings
from mkwind.schedulers.base import SchedulerJob
from mkwind.schedulers.sge import SGEScheduler
from mkite_core.tests.tempdirs import run_in_tempdir


SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
QACCT_FILE = resource_filename("mkwind.schedulers.tests.files", "sge_qacct.txt")
QSTAT_FILE = resource_filename("mkwind.schedulers.tests.files", "sge_qstat.txt")


class MockSGEScheduler(SGEScheduler):
    SUBMIT_CMD = "echo"

    def _run(self, cmd):
        if "qstat" in cmd:
            return self.qstat

        if "qacct" in cmd:
            return self.qacct

    @property
    def qacct(self):
        with open(QACCT_FILE, "r") as f:
            out = f.read()

        return out

    @property
    def qstat(self):
        with open(QSTAT_FILE, "r") as f:
            out = f.read()

        return out


class TestSGEScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockSGEScheduler(settings=settings)

    def test_gets(self):
        self.assertEqual(len(self.sched.get_running()), 2)
        self.assertEqual(len(self.sched.get_pending()), 2)
        self.assertEqual(len(self.sched.get_done()), 2)
        self.assertEqual(len(self.sched.get_error()), 0)

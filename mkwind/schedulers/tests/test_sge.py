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
QSTAT_R_FILE = resource_filename("mkwind.schedulers.tests.files", "sge_qstat_r.xml")
QSTAT_P_FILE = resource_filename("mkwind.schedulers.tests.files", "sge_qstat_p.xml")


class MockSGEScheduler(SGEScheduler):
    SUBMIT_CMD = "echo"

    def _run(self, cmd):
        if "qstat" in cmd:
            if "-s r" in cmd:
                return self._read_file(QSTAT_R_FILE)

            if "-s p" in cmd:
                return self._read_file(QSTAT_P_FILE)

        if "qacct" in cmd:
            return self._read_file(QACCT_FILE)

    def _read_file(self, file):
        with open(file, "r") as f:
            out = f.read()
        return out


class TestSGEScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockSGEScheduler(settings=settings)

    def test_get_qstat(self):
        self.assertEqual(len(self.sched.get_running()), 2)
        self.assertEqual(len(self.sched.get_pending()), 3)

    def test_get_qacct(self):
        self.assertEqual(len(self.sched.get_done()), 2)
        self.assertEqual(len(self.sched.get_error()), 1)

import os
import re
import json
from typing import List
from pathlib import Path
import unittest as ut
from unittest.mock import patch
from pkg_resources import resource_filename

from mkwind.user import EnvSettings
from mkwind.schedulers.base import SchedulerJob
from mkwind.schedulers.lsf import LsfScheduler
from mkite_core.tests.tempdirs import run_in_tempdir


SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")

STATUS = """
{
  "COMMAND":"bjobs",
  "JOBS":8,
  "RECORDS":[
    {
      "JOBID":"1",
      "QUEUE":"pbatch",
      "STAT":"PEND",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"2",
      "QUEUE":"pbatch",
      "STAT":"PEND",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"3",
      "QUEUE":"pbatch",
      "STAT":"PSUSP",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"4",
      "QUEUE":"pbatch",
      "STAT":"RUN",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"5",
      "QUEUE":"pbatch",
      "STAT":"RUN",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"6",
      "QUEUE":"pbatch",
      "STAT":"RUN",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"7",
      "QUEUE":"pbatch",
      "STAT":"DONE",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 05:55",
      "JOB_NAME":"job"
    },
    {
      "JOBID":"8",
      "QUEUE":"pbatch",
      "STAT":"EXIT",
      "JOB_GROUP":"",
      "START_TIME":"Sep 13 15:20",
      "JOB_NAME":"job"
    }
  ]
}
"""


class MockLsfScheduler(LsfScheduler):
    SUBMIT_CMD = "printf '%s ' \"${*}\""

    def _run(self, cmd):
        if self.STATUS_CMD in cmd:
            return self._run_status(cmd)

        if self.SUBMIT_CMD in cmd:
            return super()._run(cmd).strip()

        raise ValueError(f"command {cmd} does not have the expected format")

    def _run_status(self, cmd):
        if "-p" in cmd:
            return self._filter_status(["PEND"])

        if "-r" in cmd:
            return self._filter_status(["RUN"])

        if "-d" in cmd:
            return self._filter_status(["DONE", "EXIT"])

        return self._get_status()

    def _get_status(self):
        return STATUS

    def _filter_status(self, status_list: List[str]):
        status = json.loads(self._get_status())
        status["RECORDS"] = [
            job for job in status["RECORDS"] if job["STAT"] in status_list
        ]
        status["JOBS"] = len(status["RECORDS"])

        return json.dumps(status)


class TestLsfScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockLsfScheduler(settings=settings)

    @run_in_tempdir
    def test_submit(self):
        NAME = "testname"
        os.mkdir(NAME)
        Path(f"{NAME}/job.sh").touch()

        out = self.sched.submit_job(NAME)
        expected = f"-J testname"

        self.assertEqual(out, expected)

    def test_status(self):
        sjobs = self.sched.get_all()
        self.assertEqual(len(sjobs), 8)

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
        self.assertEqual(len(sjobs), 2)

    def test_queued(self):
        sjobs = self.sched.get_queued()
        self.assertEqual(len(sjobs), 6)

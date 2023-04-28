import os
import unittest as ut
from unittest.mock import patch

from pkg_resources import resource_filename
from mkwind.user import EnvSettings
from mkwind.schedulers.base import SchedulerJob, Scheduler


SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")


class MockScheduler(Scheduler):
    def submit_job(self, job):
        pass

    def get_all(self, job):
        pass

    def get_queued(self):
        pass

    def get_pending(self):
        pass

    def get_running(self):
        pass

    def get_done(self):
        pass

    def get_error(self):
        pass

    def get_failed(self):
        pass


class TestSchedulerJob(ut.TestCase):
    def setUp(self):
        self.example = {
            "id": "12345678",
            "name": "7ef649a3",
            "start_time": "N/A",
            "partition": "pdebug",
            "group": "normal",
            "status": "PENDING",
        }

    def test_schedjob(self):
        sjob = SchedulerJob(**self.example)
        self.assertEqual(sjob.id, 12345678)


class TestScheduler(ut.TestCase):
    def setUp(self):
        settings = EnvSettings.from_file(SETTINGS)
        self.sched = MockScheduler(settings=settings)

    def test_run(self):
        cmd = 'echo "testing"'
        out = self.sched._run(cmd)

        self.assertEqual(out, "testing\n")

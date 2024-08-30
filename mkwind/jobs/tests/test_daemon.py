import os
import subprocess
from distutils.dir_util import copy_tree

import unittest as ut
from unittest.mock import patch, Mock, MagicMock
from pkg_resources import resource_filename

from mkite_core.models import Status
from mkite_core.external import load_config
from mkite_core.tests.tempdirs import run_in_tempdir

from mkwind.user import EnvSettings
from mkwind.schedulers import SchedulerJob, SchedulerError
from mkwind.schedulers.tests.test_slurm import MockSlurmScheduler
from mkwind.jobs.daemon import JobDaemon


EXAMPLE_JOBS_PATH = resource_filename("mkwind.tests.files", "example_jobs")
INFO_PATH = resource_filename("mkwind.tests.files", "jobinfo.json")
BUILD_CONFIG = resource_filename("mkwind.tests.files.clusters", "cluster1.yaml")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
ENGINE = resource_filename("mkwind.tests.files.engines", "local.yaml")


class TestDaemon(ut.TestCase):
    def get_settings(self):
        return EnvSettings.from_file(SETTINGS)

    def copy_example_jobs(self, settings: EnvSettings):
        engine_cfg = load_config(ENGINE)
        copy_tree(str(EXAMPLE_JOBS_PATH), str(engine_cfg["root_path"]))

    def get_daemon(self):
        settings = self.get_settings()
        scheduler = MockSlurmScheduler(settings)
        self.copy_example_jobs(settings)

        return JobDaemon(
            scheduler=scheduler,
            settings=settings,
            logger_stdout=False,
        )

    @run_in_tempdir
    def test_instantiate(self):
        daemon = self.get_daemon()

    @run_in_tempdir
    def test_submit_avoidance(self):
        daemon = self.get_daemon()
        daemon.settings.MAX_PENDING = 0
        submitted = daemon.submit()

        self.assertEqual(submitted, [])

    @run_in_tempdir
    def test_submit(self):
        daemon = self.get_daemon()
        daemon.settings.MAX_PENDING = 10
        submitted = daemon.submit()

        self.assertEqual(submitted, ["test_recipe_7615c560_1658944102"])

    @run_in_tempdir
    def test_submit_with_error(self):
        def error_submission(*args, **kwargs):
            raise SchedulerError("error")

        daemon = self.get_daemon()
        daemon.scheduler.submit_job = error_submission
        daemon.error_sleep = 0

        submitted = daemon.submit()
        jobs_ready = daemon.consumer.list_queue(Status.READY.value)
        jobs_doing = daemon.consumer.list_queue(Status.DOING.value)

        self.assertEqual(len(jobs_ready), 1)
        self.assertEqual(len(jobs_doing), 1)

    @run_in_tempdir
    def test_process_done(self):
        done_info = SchedulerJob(
            id=1011123,
            name="test_recipe_9c60037b_1658944102",
            start_time="2022-07-26",
            partition="pdebug",
            group="normal",
            status="COMPLETED",
        )

        mock_scheduler = Mock()
        mock_scheduler.get_done.return_value = [done_info]

        daemon = self.get_daemon()
        daemon.scheduler = mock_scheduler

        done = daemon.process_done()
        self.assertEqual(done, ["test_recipe_9c60037b_1658944102"])

    @run_in_tempdir
    def test_process_error(self):
        info = SchedulerJob(
            id=1011123,
            name="test_recipe_9c60037b_1658944102",
            start_time="2022-07-26",
            partition="pdebug",
            group="normal",
            status="CANCELLED",
        )

        mock_scheduler = MagicMock()
        mock_scheduler.get_error.return_value = [info]

        daemon = self.get_daemon()
        daemon.scheduler = mock_scheduler

        error = daemon.process_error()
        self.assertEqual(error, ["test_recipe_9c60037b_1658944102"])

    @run_in_tempdir
    def test_process_failed(self):
        info = SchedulerJob(
            id=1011123,
            name="test_recipe_9c60037b_1658944102",
            start_time="2022-07-26",
            partition="pdebug",
            group="normal",
            status="PREEMPTED",
        )

        mock_scheduler = MagicMock()
        mock_scheduler.get_failed.return_value = [info]

        daemon = self.get_daemon()
        daemon.scheduler = mock_scheduler

        error = daemon.process_failed()
        self.assertEqual(error, ["test_recipe_9c60037b_1658944102"])

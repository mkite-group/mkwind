import os
import unittest as ut
from unittest.mock import patch
from distutils.dir_util import copy_tree
from pkg_resources import resource_filename

from mkwind.user import EnvSettings
from mkite_core.models import Status
from mkite_core.external import load_config
from mkwind.postprocess.daemon import PostprocessDaemon
from mkite_core.tests.tempdirs import run_in_tempdir


EXAMPLE_SETTINGS_PATH = resource_filename(
    "mkwind.tests.files.clusters", "cluster1.yaml"
)
EXAMPLE_JOBS_PATH = resource_filename("mkwind.tests.files", "example_jobs")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
ENGINE = resource_filename("mkwind.tests.files.engines", "local.yaml")


class TestDaemon(ut.TestCase):
    def copy_example_jobs(self, settings: EnvSettings):
        engine_cfg = load_config(ENGINE)
        copy_tree(str(EXAMPLE_JOBS_PATH), str(engine_cfg["root_path"]))

    def get_settings(self):
        return EnvSettings.from_file(SETTINGS)

    def get_daemon(self, settings: EnvSettings):
        return PostprocessDaemon.from_settings(
            settings=settings,
            compress=True,
            logger_stdout=False,
        )

    @run_in_tempdir
    def test_postprocess(self):
        settings = self.get_settings()
        self.copy_example_jobs(settings)
        daemon = self.get_daemon(settings)

        done, errors = daemon.postprocess()

        done_folders = daemon.postproc.src.list_queue(Status.DONE.value)
        self.assertEqual(done_folders, [])

        parsing_folders = [
            "recipe_" + fname.split("-")[0]
            for fname in daemon.postproc.dst.list_queue(Status.PARSING.value)
        ]
        self.assertEqual(parsing_folders, done)

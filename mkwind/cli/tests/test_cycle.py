import os
import unittest as ut
from unittest.mock import patch
from distutils.dir_util import copy_tree
from pkg_resources import resource_filename

from mkwind.user import EnvSettings
from mkwind.templates import Template
from mkwind.builder.daemon import BuilderDaemon
from mkite_core.models import Status
from mkite_core.tests.tempdirs import run_in_tempdir
from mkite_core.external import load_config
from mkwind.cli.cycle import _get_managers, _run_cycle, _cycle


EXAMPLE_SETTINGS_PATH = resource_filename("mkwind.tests.files.clusters", "cluster1.yaml")
EXAMPLE_JOBS_PATH = resource_filename("mkwind.tests.files", "example_jobs")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
ENGINE = resource_filename("mkwind.tests.files.engines", "local.yaml")


class TestCycle(ut.TestCase):
    def copy_example_jobs(self, settings: EnvSettings):
        engine_cfg = load_config(ENGINE)
        copy_tree(str(EXAMPLE_JOBS_PATH), str(engine_cfg["root_path"]))

    def get_settings(self):
        return EnvSettings.from_file(SETTINGS)

    def get_template(self):
        return Template.from_name("slurm.sh")

    @run_in_tempdir
    def test_get_managers(self):
        # TODO: fill out here
        pass

    @run_in_tempdir
    def test_run_cycle(self):
        # TODO: fill out here
        pass

    @run_in_tempdir
    def test_example(self):
        # TODO: Read this portion to understand how to make a unittest
        settings = self.get_settings()
        self.copy_example_jobs(settings)
        daemon = self.get_daemon(settings)

        built = daemon.build()
        built = built[0]

        to_build = daemon.builder.src.list_queue("vasp.example")
        self.assertEqual(to_build, [])
        self.assertTrue(os.path.exists(built))

        files = set(os.listdir(built))
        self.assertEqual(files, {"jobinfo.json", "job.sh", "runstats.json"})

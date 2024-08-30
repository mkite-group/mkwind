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


EXAMPLE_SETTINGS_PATH = resource_filename("mkwind.tests.files.clusters", "cluster1.yaml")
EXAMPLE_JOBS_PATH = resource_filename("mkwind.tests.files", "example_jobs")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")
ENGINE = resource_filename("mkwind.tests.files.engines", "local.yaml")


class TestDaemon(ut.TestCase):
    def copy_example_jobs(self, settings: EnvSettings):
        engine_cfg = load_config(ENGINE)
        copy_tree(str(EXAMPLE_JOBS_PATH), str(engine_cfg["root_path"]))

    def get_settings(self):
        return EnvSettings.from_file(SETTINGS)

    def get_template(self):
        return Template.from_name("slurm.sh")

    def get_daemon(self, settings: EnvSettings):
        return BuilderDaemon.from_settings(
            settings=settings,
            logger_stdout=False,
            delete_on_build=True,
        )

    @run_in_tempdir
    def test_build(self):
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

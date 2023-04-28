import os
import unittest as ut
from unittest.mock import patch
from mkite_core.external import load_config
from pkg_resources import resource_filename

from mkite_core.models import JobInfo
from mkwind.user import EnvSettings
from mkwind.builder.settings import JobSettings, AllJobSettings

from mkite_core.tests.tempdirs import run_in_tempdir

INFO_PATH = resource_filename("mkwind.tests.files", "jobinfo.json")
JOB_SETTINGS_PATH = resource_filename("mkwind.tests.files.clusters", "recipe.yaml")
ALL_SETTINGS_PATH = resource_filename("mkwind.tests.files", "clusters")
EXAMPLE_SETTINGS_PATH = resource_filename(
    "mkwind.tests.files.clusters", "cluster1.yaml"
)

ENVIRONMENT = {
    "USER": "user",
    "ROOT_PATH": ".",
    "LOG_PATH": "./mkwind.log",
    "BUILD_LOG_PATH": "./mkwind-build.log",
    "BUILD_CONFIG": EXAMPLE_SETTINGS_PATH,
    "ARCHIVE_PATH": "./archive",
    "QUEUE_PATH": ".",
}

class TestJobSettings(ut.TestCase):
    def test_load(self):
        js = JobSettings.from_yaml(JOB_SETTINGS_PATH)
        expected = dict(load_config(JOB_SETTINGS_PATH))

        for k, v in expected.items():
            self.assertEqual(getattr(js, k), v)

    def test_choices(self):
        choices = set(JobSettings.get_choices(ALL_SETTINGS_PATH))
        expected = {
            "cluster1.yaml",
            "recipe.yaml",
            "cluster2/main.yaml",
        }
        self.assertEqual(choices, expected)


class TestAllJobSettings(ut.TestCase):
    @patch.dict(os.environ, ENVIRONMENT)
    def setUp(self):
        self.info = JobInfo.from_json(INFO_PATH)
        self.recipe_settings = AllJobSettings.from_file(EXAMPLE_SETTINGS_PATH)

    def test_get_recipe(self):
        settings = self.recipe_settings.get_recipe_settings(self.info)
        expected = dict(load_config(EXAMPLE_SETTINGS_PATH)["default"])

        for k, v in expected.items():
            self.assertEqual(getattr(settings, k), v)

    def test_get_recipe_package(self):
        self.info.recipe["name"] = "vasp.pbe.relax"
        settings = self.recipe_settings.get_recipe_settings(self.info)
        expected = dict(load_config(EXAMPLE_SETTINGS_PATH)["vasp"])

        for k, v in expected.items():
            self.assertEqual(getattr(settings, k), v)

    def test_has_recipe(self):
        has_recipe = self.recipe_settings.config_has_recipe("vasp.pbe.relax")
        self.assertTrue(has_recipe)

        has_recipe = self.recipe_settings.config_has_recipe("vasp")
        self.assertTrue(has_recipe)

        has_recipe = self.recipe_settings.config_has_recipe("nonexisting")
        self.assertFalse(has_recipe)

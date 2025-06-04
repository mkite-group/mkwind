import os
from pkg_resources import resource_filename

import unittest as ut
from freezegun import freeze_time

from mkite_core.models import JobInfo, Status
from mkwind.templates import Template
from mkwind.user import EnvSettings
from mkite_engines import LocalConsumer, EngineRoles, instantiate_from_path
from mkwind.builder import JobBuilder, JobSettings
from mkite_core.tests.tempdirs import run_in_tempdir


INFO_PATH = resource_filename("mkwind.tests.files", "jobinfo.json")
BUILD_CONFIG = resource_filename("mkwind.tests.files.clusters", "cluster1.yaml")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")


class TestBuilder(ut.TestCase):
    def setUp(self):
        self.info = JobInfo.from_json(INFO_PATH)
        self.info.recipe["package"] = "vasp"
        self.info.recipe["name"] = "vasp.pbe.relax"

        self.template = Template.from_name("slurm.sh")
        self.settings = EnvSettings.from_file(SETTINGS)

    def get_builder(self, explicit_config: bool = False, delete_on_build: bool = True):
        src = instantiate_from_path(
            self.settings.ENGINE_EXTERNAL,
            role=EngineRoles.consumer,
        )
        dst = instantiate_from_path(
            self.settings.ENGINE_LOCAL,
            role=EngineRoles.producer,
        )
        dst.add_queue(Status.READY)

        builder = JobBuilder(
            src_engine=src,
            dst_engine=dst,
            settings=self.settings,
            template=self.template,
            explicit_config=explicit_config,
            delete_on_build=delete_on_build,
        )
        return builder

    @run_in_tempdir
    def test_setup_queues(self):
        builder = self.get_builder()
        dirs = sorted(os.listdir("."))
        expected = ["building", "queue-ready"]

        self.assertEqual(dirs, expected)

    @run_in_tempdir
    def test_make_folder(self):
        builder = self.get_builder()

        with freeze_time("2022-07-26"):
            path = builder.make_folder(self.info, ".")

        TIMESTAMP = 1658793600
        expected = f"vasp.pbe.relax_7615c560_{TIMESTAMP}"

        self.assertEqual(os.path.basename(path), expected)

    @run_in_tempdir
    def test_get_settings(self):
        builder = self.get_builder()

        settings = builder.get_settings(self.info)
        expected = JobSettings.from_file_choices(
            BUILD_CONFIG, choice="vasp", with_default=True
        )

        self.assertEqual(settings, expected)

    @run_in_tempdir
    def test_write_template(self):
        builder = self.get_builder()
        job_folder = os.path.join(builder.src.root_path, "test_job")
        os.mkdir(job_folder)
        settings = JobSettings.from_file_choices(
            BUILD_CONFIG, choice="vasp", with_default=True
        )

        dst = builder.write_template(job_folder, settings)
        self.assertEqual(os.path.basename(dst), Template.FILENAME)

        with open(dst, "r") as f:
            job_script = f.read()

        expected_script = "#!/bin/bash -l\n\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node=36\n#SBATCH --time=24:00:00\n#SBATCH --partition=pdebug\n#SBATCH --account=vasp_default\nmodule load vasp\n\nsrun -n$SLURM_NTASKS vasp\n"

        self.assertEqual(job_script, expected_script)

    @run_in_tempdir
    def test_build(self):
        builder = self.get_builder()

        with freeze_time("2022-07-26"):
            path = builder.build_job(self.info)

        TIMESTAMP = 1658793600
        expected = f"vasp.pbe.relax_{self.info.uuid_short}_{TIMESTAMP}"

        self.assertEqual(os.path.basename(path), expected)

        files = set(os.listdir(path))
        expected_files = {
            Template.FILENAME,
            JobInfo.file_name(),
            JobSettings.file_name(),
        }
        self.assertEqual(files, expected_files)

    @run_in_tempdir
    def test_build_explicit_passing(self):
        builder = self.get_builder(explicit_config=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        to_build = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(to_build, ["jobinfo.json"])

        built = builder.build_all()
        self.assertEqual(len(built), 1)

    @run_in_tempdir
    def test_delete_on_build(self):
        builder = self.get_builder(explicit_config=True, delete_on_build=False)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        to_build = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(to_build, ["jobinfo.json"])

        built = builder.build_all(max_build=1)
        self.assertEqual(len(built), 1)

        to_build = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(to_build, ["jobinfo.json"])

    @run_in_tempdir
    def test_build_explicit_not_passing(self):
        builder = self.get_builder(explicit_config=True)
        recipe = "nonexisting"
        builder.src.add_queue(recipe)
        self.info.recipe["name"] = recipe

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        to_build = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(to_build, ["jobinfo.json"])

        built = builder.build_all()
        self.assertEqual(len(built), 0)

    @run_in_tempdir
    def test_build_all_max_build(self):
        builder = self.get_builder(explicit_config=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        
        # Add multiple jobs to the queue
        for i in range(3):
            info_copy = JobInfo.from_json(INFO_PATH)
            info_copy.recipe["package"] = "vasp"
            info_copy.recipe["name"] = "vasp.pbe.relax"
            info_copy.job["uuid"] = f"test-uuid-{i}"
            info_copy.to_json(f"building/{recipe_queue}/jobinfo_{i}.json")

        to_build = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(len(to_build), 3)

        # Test max_build limit
        built = builder.build_all(max_build=2)
        self.assertEqual(len(built), 2)

        # Check that one job remains in the queue
        remaining = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(len(remaining), 1)

    @run_in_tempdir
    def test_build_one_with_recipe(self):
        builder = self.get_builder(explicit_config=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        key, info, job_folder = builder.build_one(recipe=recipe)
        
        self.assertIsNotNone(key)
        self.assertIsNotNone(info)
        self.assertIsNotNone(job_folder)
        self.assertEqual(info.recipe["name"], recipe)

        # Check that job folder was created with expected files
        files = set(os.listdir(job_folder))
        expected_files = {
            Template.FILENAME,
            JobInfo.file_name(),
            JobSettings.file_name(),
        }
        self.assertEqual(files, expected_files)

    @run_in_tempdir
    def test_build_one_without_recipe(self):
        builder = self.get_builder(explicit_config=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        key, info, job_folder = builder.build_one()
        
        self.assertIsNotNone(key)
        self.assertIsNotNone(info)
        self.assertIsNotNone(job_folder)

    @run_in_tempdir
    def test_build_one_empty_queue(self):
        builder = self.get_builder(explicit_config=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        # Don't add any jobs to the queue
        key, info, job_folder = builder.build_one(recipe=recipe)
        
        self.assertIsNone(key)
        self.assertIsNone(info)
        self.assertIsNone(job_folder)

    @run_in_tempdir
    def test_build_one_delete_on_build(self):
        builder = self.get_builder(explicit_config=True, delete_on_build=True)
        recipe = self.info.recipe["name"]
        builder.src.add_queue(recipe)

        recipe_queue = builder.src.format_queue_name(recipe)
        self.info.to_json(f"building/{recipe_queue}/jobinfo.json")

        to_build_before = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(len(to_build_before), 1)

        key, info, job_folder = builder.build_one(recipe=recipe)
        
        # Check that job was deleted from source queue
        to_build_after = os.listdir(f"building/{recipe_queue}")
        self.assertEqual(len(to_build_after), 0)

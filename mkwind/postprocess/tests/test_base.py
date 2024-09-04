import os
import unittest as ut
from pathlib import Path
from unittest.mock import patch

from freezegun import freeze_time
from mkite_core.external import load_config
from mkite_core.models import JobInfo, JobResults, Status
from mkite_core.tests.tempdirs import run_in_tempdir
from mkite_engines import EngineRoles, instantiate_from_path
from mkwind.postprocess.base import JobPostprocessor, PostprocessError
from mkwind.user import EnvSettings
from pkg_resources import resource_filename


INFO_PATH = resource_filename("mkwind.tests.files", "jobresults.json")
BUILD_CONFIG = resource_filename("mkwind.tests.files.clusters", "cluster1.yaml")
SETTINGS = resource_filename("mkwind.tests.files", "settings.yaml")


class TestPostprocessor(ut.TestCase):
    def get_postproc(self):
        settings = self.get_settings()
        src = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.consumer)
        src.add_queue(Status.DONE)

        dst = instantiate_from_path(settings.ENGINE_EXTERNAL, role=EngineRoles.producer)
        dst.add_queue(Status.PARSING)

        err = instantiate_from_path(settings.ENGINE_EXTERNAL, role=EngineRoles.producer)
        err.add_queue(Status.ERROR)

        arch = instantiate_from_path(settings.ENGINE_ARCHIVE, role=EngineRoles.producer)
        arch.add_queue(Status.ARCHIVE)

        postproc = JobPostprocessor(
            src_engine=src,
            dst_engine=dst,
            error_engine=err,
            archive_engine=arch,
        )

        queue_done = src.format_queue_name(Status.DONE.value)
        os.mkdir(f"{queue_done}/{self.jobfolder}")
        self.info.to_json(f"{queue_done}/{self.jobfolder}/jobresults.json")

        os.mkdir(f"{queue_done}/invalid_folder")

        return postproc

    def get_settings(self):
        return EnvSettings.from_file(SETTINGS)

    def setUp(self):
        self.info = JobResults.from_json(INFO_PATH)
        self.jobfolder = "recipe_ebeae8e2"

    def get_folder(self, postproc: JobPostprocessor, folder: str):
        return os.path.join(
            postproc.src.get_queue_path(Status.DONE.value),
            folder,
        )

    @run_in_tempdir
    def test_get_jobresults(self):
        postproc = self.get_postproc()

        good_path = self.get_folder(postproc, self.jobfolder)
        info = postproc.get_jobresults(good_path)
        self.assertIsInstance(info, JobResults)

        bad_path = self.get_folder(postproc, "invalid_folder")
        with self.assertRaises(FileNotFoundError):
            postproc.get_jobresults(bad_path)

    @run_in_tempdir
    def test_get_jobid(self):
        postproc = self.get_postproc()

        path = self.get_folder(postproc, self.jobfolder)
        jobid = postproc.get_jobid(self.info, path)
        self.assertEqual(jobid, self.info.job["uuid"])

        self.info.job.pop("uuid")
        jobid = postproc.get_jobid(self.info, path)
        self.assertEqual(jobid, str(self.info.job["id"]))

        self.info.job.pop("id")
        jobid = postproc.get_jobid(self.info, path)
        self.assertEqual(jobid, os.path.basename(path))

    @run_in_tempdir
    def test_compress_folder(self):
        postproc = self.get_postproc()

        folder = self.get_folder(postproc, self.jobfolder)
        name = self.info.job["uuid"]

        tar_path = postproc.compress_folder(folder, name=name)
        archived = postproc.archive.list_queue(Status.ARCHIVE)
        expected = [os.path.basename(tar_path)]
        self.assertEqual(archived, expected)

    @run_in_tempdir
    def test_postprocess_job(self):
        postproc = self.get_postproc()

        folder = self.get_folder(postproc, self.jobfolder)
        results_path = postproc.postprocess_job(folder)

        processed = postproc.dst.list_queue(Status.PARSING.value)
        expected = [self.info.job["uuid"] + ".json"]
        self.assertEqual(processed, expected)

        archived = postproc.archive.list_queue(Status.ARCHIVE)
        expected = [self.info.job["uuid"] + ".tar.gz"]
        self.assertEqual(archived, expected)

    @run_in_tempdir
    def test_postprocess_all(self):
        postproc = self.get_postproc()

        done, errors = postproc.postprocess_all()

        expected_done = [self.jobfolder]
        self.assertEqual(done, expected_done)

        expected_errors = ["invalid_folder"]
        self.assertEqual(errors, expected_errors)

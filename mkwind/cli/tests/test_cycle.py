import os
import unittest as ut
from unittest.mock import patch, MagicMock
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

    def get_daemon(self, settings):
        """Helper method to create a daemon for testing."""
        return BuilderDaemon.from_settings(settings)

    @run_in_tempdir
    def test_get_managers(self):
        """Test that _get_managers properly initializes builder and postprocessor."""
        settings_obj = self.get_settings()
        dst = "test_dst"
        os.makedirs(dst, exist_ok=True)
        
        _, builder, pproc = _get_managers(None, dst)
        
        # Verify settings object
        self.assertIsInstance(settings_obj, EnvSettings)
        
        # Verify builder is properly configured
        self.assertIsNotNone(builder)
        self.assertEqual(builder.explicit_config, True)
        self.assertEqual(builder.delete_on_build, False)
        
        # Verify postprocessor is properly configured
        self.assertIsNotNone(pproc)
        self.assertEqual(pproc.compress, True)
        self.assertEqual(pproc.allow_restart, False)

    @run_in_tempdir
    @patch('mkite_core.plugins.get_recipe')
    def test_run_cycle(self, mock_get_recipe):
        """Test that _run_cycle properly builds, runs, and postprocesses a job."""
        from mkwind.cli.tests.dummy_job import DummyRecipe
        
        # Mock the recipe loading
        mock_get_recipe.return_value.load.return_value = DummyRecipe
        
        # Create mock builder and postprocessor
        mock_builder = MagicMock()
        mock_pproc = MagicMock()
        
        # Mock builder.build_one to return test data
        test_folder = "test_job_folder"
        os.makedirs(test_folder, exist_ok=True)
        
        # Create a mock JobInfo
        from mkite_core.models import JobInfo
        mock_info = JobInfo(
            job="test_job_123",
            recipe={"name": "dummy_recipe", "package": "test"},
            inputs=[],
            options={}
        )
        
        mock_builder.build_one.return_value = ("test_key", mock_info, test_folder)
        
        # Run the cycle
        _run_cycle(mock_builder, mock_pproc, "dummy_recipe")
        
        # Verify that build_one was called
        mock_builder.build_one.assert_called_once_with("dummy_recipe")
        
        # Verify that postprocess_one was called with the correct folder
        mock_pproc.postprocess_one.assert_called_once_with(test_folder)
        
        # Verify that the dummy job created its output files
        self.assertTrue(os.path.exists(os.path.join(test_folder, "dummy_output.json")))
        self.assertTrue(os.path.exists(os.path.join(test_folder, "job_complete.txt")))

    @run_in_tempdir
    @patch('mkite_core.plugins.get_recipe')
    def test_run_cycle_with_job_failure(self, mock_get_recipe):
        """Test that _run_cycle handles job execution failures gracefully."""
        # Create a failing recipe
        class FailingRecipe:
            def __init__(self, job_info):
                self.job_info = job_info
            
            def run(self):
                raise RuntimeError("Simulated job failure")
        
        mock_get_recipe.return_value.load.return_value = FailingRecipe
        
        # Create mock builder and postprocessor
        mock_builder = MagicMock()
        mock_pproc = MagicMock()
        
        test_folder = "test_job_folder"
        os.makedirs(test_folder, exist_ok=True)
        
        from mkite_core.models import JobInfo
        mock_info = JobInfo(
            job="test_job_123",
            recipe={"name": "failing_recipe", "package": "test"},
            inputs=[],
            options={}
        )
        
        mock_builder.build_one.return_value = ("test_key", mock_info, test_folder)
        
        with patch('builtins.print') as mock_print:
            # Run the cycle - should handle the exception gracefully
            _run_cycle(mock_builder, mock_pproc, "failing_recipe")
            
            # Verify error message was printed
            mock_print.assert_any_call(f"ERROR: Failed to run the job {mock_info.job}")
            
            # Postprocess should still be called
            mock_pproc.postprocess_one.assert_called_once_with(test_folder)

    @run_in_tempdir
    @patch('mkite_core.plugins.get_recipe')
    def test_run_cycle_with_postprocess_failure(self, mock_get_recipe):
        """Test that _run_cycle handles postprocessing failures gracefully."""
        from mkwind.cli.tests.dummy_job import DummyRecipe
        
        mock_get_recipe.return_value.load.return_value = DummyRecipe
        
        # Create mock builder and postprocessor
        mock_builder = MagicMock()
        mock_pproc = MagicMock()
        
        test_folder = "test_job_folder"
        os.makedirs(test_folder, exist_ok=True)
        
        from mkite_core.models import JobInfo
        mock_info = JobInfo(
            job="test_job_123",
            recipe={"name": "dummy_recipe", "package": "test"},
            inputs=[],
            options={}
        )
        
        mock_builder.build_one.return_value = ("test_key", mock_info, test_folder)
        mock_pproc.postprocess_one.side_effect = RuntimeError("Postprocess failed")
        
        with patch('builtins.print') as mock_print:
            # Run the cycle - should handle the postprocess exception gracefully
            _run_cycle(mock_builder, mock_pproc, "dummy_recipe")
            
            # Verify error message was printed
            mock_print.assert_any_call(f"ERROR: Failed to postprocess the job {mock_info.job}")

    @run_in_tempdir
    def test_run_cycle_no_job_available(self):
        """Test that _run_cycle handles the case when no job is available to build."""
        # Create mock builder and postprocessor
        mock_builder = MagicMock()
        mock_pproc = MagicMock()
        
        # Mock builder.build_one to return None (no job available)
        mock_builder.build_one.return_value = (None, None, None)
        
        # Run the cycle
        result = _run_cycle(mock_builder, mock_pproc, "nonexistent_recipe")
        
        # Verify that postprocess_one was not called
        mock_pproc.postprocess_one.assert_not_called()
        
        # Function should return None
        self.assertIsNone(result)

    @run_in_tempdir
    @patch('mkwind.cli.cycle._run_cycle')
    def test_cycle_integration(self, mock_run_cycle):
        """Test the main _cycle function integration."""
        dst = "test_dst"
        recipe = "test_recipe"
        
        # Run the cycle function
        _cycle(recipe, None, dst)
        
        # Verify that _run_cycle was called with the correct arguments
        mock_run_cycle.assert_called_once()
        args = mock_run_cycle.call_args[0]
        self.assertEqual(len(args), 3)  # builder, pproc, recipe
        self.assertEqual(args[2], recipe)  # recipe should be the third argument

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

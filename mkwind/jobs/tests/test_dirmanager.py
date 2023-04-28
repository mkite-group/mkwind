import os
import unittest as ut
from mkwind.jobs.dirmanager import TemporaryChdir

from mkite_core.tests.tempdirs import run_in_tempdir


class TestTempChdir(ut.TestCase):
    @run_in_tempdir
    def test_chdir(self):
        cwd = os.getcwd()

        workdir = "test"
        workdir_abs = os.path.abspath(workdir)
        os.mkdir(workdir_abs)

        with TemporaryChdir(to=workdir):
            current_dir = os.getcwd()
            self.assertEqual(current_dir, workdir_abs)

        self.assertEqual(os.getcwd(), cwd)

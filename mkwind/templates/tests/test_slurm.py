import os
import unittest as ut
from mkite_core.external import load_config
from pkg_resources import resource_filename

from mkwind.templates import Template
from mkite_core.tests.tempdirs import run_in_tempdir

CONFIG_PATH = resource_filename("mkwind.tests.files.clusters", "recipe.yaml")
TEMPLATE_PATH = resource_filename("mkwind.templates", "slurm.sh")


class TestTemplate(ut.TestCase):
    def setUp(self):
        self.inputs = load_config(CONFIG_PATH)
        self.template = Template(TEMPLATE_PATH)

    def test_render(self):
        out = self.template.render(self.inputs)
        expected = "#!/bin/bash -l\n\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node=8\n#SBATCH --time=30:00\n#SBATCH --partition=pdebug\n#SBATCH --account=test\nmodule load vasp\n\nsrun -n$SLURM_NTASKS vasp\ntouch mkwind-complete\n\n"

        self.assertEqual(out, expected)

    @run_in_tempdir
    def test_render_to(self):
        dst = self.template.render_to(self.inputs, ".")

        self.assertTrue(os.path.exists(Template.FILENAME))

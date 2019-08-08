import os
import time

from click.testing import CliRunner
from pathlib import Path
from unittest import TestCase
from maniplecli.commands.deploy import cli as deploy
from maniplecli.commands.config import cli as con
from maniplecli.util.shell import Shell

# TODO: compare folders with filecmp


class TestDeployCommand(TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.file_dir = Path(__file__).parent

    def tearDown(self):
        self.runner.invoke(con, ['-c'], input='y')
        Shell.run('terraform destroy -auto-approve', os.getcwd())

    # Tests both deploy --new-function and --update becuase all resources
    # are destroyed at the end of the test so can only update when it's created
    def test_deploy_new_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(con, ['--name', 'basic'])
        result_new_function = self.runner.invoke(deploy, ['-n'], input='2')
        self.assertEquals(result_new_function.exit_code, 0)
        time.sleep(3)
        result_update = self.runner.invoke(deploy, ['-u'])
        self.assertEquals(result_update.exit_code, 0)

    def test_deploy_all_new_modules_mult_folder(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))
        self.runner.invoke(con, ['-c'], input='y')
        result_new_function = self.runner.invoke(deploy, ['--all', '-n'])
        self.assertEquals(result_new_function.exit_code, 0)

import os

from click.testing import CliRunner
from pathlib import Path
from unittest import TestCase
from maniplecli.commands.pack import cli as pack
from maniplecli.commands.config import cli as con

# TODO: compare folders with filecmp


class TestPackCommand(TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.file_dir = Path(__file__).parent

    def tearDown(self):
        self.runner.invoke(con, ['-c'], input='y')

    # Forces 
    def test_create_package_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(con, ['--name', 'basic'])
        result = self.runner.invoke(pack, ['-c'], input='2')
        self.assertEquals(result.exit_code, 0)

    def test_create_package_basic_dir(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_dir'))        
        self.runner.invoke(con, ['--name', 'basic_dir'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)

    def test_create_package_basic_multiple(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_multiple'))        
        self.runner.invoke(con, ['--name', 'fn_one'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)

    def test_create_package_module_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_basic'))        
        self.runner.invoke(con, ['--name', 'mod_basic'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)

    def test_create_package_module_mult(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult'))        
        self.runner.invoke(con, ['--name', 'module_mult_one'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)            

    def test_create_package_module_mult_folder_dir(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))        
        self.runner.invoke(con, ['--name', 'module_mult_folder_dir'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)

    def test_create_package_module_mult_folder_file(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))        
        self.runner.invoke(con, ['--name', 'module_mult_folder_file'])
        result = self.runner.invoke(pack, ['-c'])
        self.assertEquals(result.exit_code, 0)

    def test_update_script_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(con, ['--name', 'basic'])
        result = self.runner.invoke(pack, ['-us'])
        self.assertEquals(result.exit_code, 0)

    def test_update_script_basic_dir(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_dir'))        
        self.runner.invoke(con, ['--name', 'basic_dir'])
        result = self.runner.invoke(pack, ['-us'])
        self.assertEquals(result.exit_code, 0)       

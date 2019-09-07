import os

from click.testing import CliRunner
from pathlib import Path
from unittest import TestCase
from maniplecli.commands.config import cli
from maniplecli.util.tf_converter import TerraformConverter
from maniplecli.util.config_loader import ConfigLoader


class TestTerraformConverter(TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.file_dir = Path(__file__).parent
        self.converter = TerraformConverter()
        
    def get_config(self, attribute):
        return ConfigLoader.load_config()

    def test_resource_get_resource_attrs(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(cli, ['--name', 'basic'])
        config = ConfigLoader.add_defaults()
        tf = TerraformConverter.load_terraform(config['tf_file'])
        res = self.converter.get_resource_attrs(tf, config['name'])
        self.assertEquals(res['function_name'], 'basic')
        self.assertEquals(res['handler'], 'basic.handler')
        self.assertEquals(res['runtime'], 'python3.6')
        self.assertEquals(res['timeout'], 1)
        self.assertEquals(res['memory_size'], 128)

    def test_module_get_resource_attrs(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_basic'))
        self.runner.invoke(cli, ['--name', 'mod_basic'])
        config = ConfigLoader.add_defaults()
        res = self.converter.get_resource_attrs(config['tf_file'], config['name'])
        self.assertEquals(res['function_name'], 'mod_basic')
        self.assertEquals(res['handler'], 'mod_basic.handler')
        self.assertEquals(res['runtime'], 'python3.6')
        self.assertEquals(res['timeout'], '900')

    def test_module_to_cloudformation(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_basic'))
        self.runner.invoke(cli, ['--name', 'mod_basic'])
        config = ConfigLoader.add_defaults()
        res = self.converter.to_cloudformation(config)
        self.assertEquals(res['Properties']['FunctionName'], 'mod_basic')
        self.assertEquals(res['Properties']['Handler'], 'mod_basic.handler')
        self.assertEquals(res['Properties']['Runtime'], 'python3.6')
        self.assertEquals(res['Properties']['Timeout'], '900')
        self.assertEquals(res['Properties']['MemorySize'], '900')
        self.assertEquals(res['Properties']['Code'],
                          config['package'] + '.zip')

    def test_env_vars(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_env_vars'))
        self.runner.invoke(cli, ['--name', 'basic'])
        config = ConfigLoader.add_defaults()
        res = self.converter.to_cloudformation(config)
        self.assertEquals(res['Properties']['Environment'],
                          {'variables': {'foo': 'bar'}})

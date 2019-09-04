import os

from click.testing import CliRunner
from pathlib import Path
from unittest import TestCase
from maniplecli.commands.config import cli
from maniplecli.util.config_loader import ConfigLoader


class TestConfigLoader(TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.file_dir = Path(__file__).parent

    def get_config(self, attribute):
        return ConfigLoader.load_config()

    def check_config(self, config, name, req_path, bucket, key, script):
        self.assertEquals(config['name'], name)
        self.assertEquals(config['requirements'], req_path)
        self.assertEquals(config['s3_bucket'], bucket)
        self.assertEquals(config['s3_key'], key)
        self.assertEquals(config['script'], script)
        self.assertTrue(Path(config['package']).exists())

    def test_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(cli, ['--name', 'basic'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'basic',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/basic.zip',
            Path('basic.py').resolve().__str__()
        )

    def test_basic_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic'))
        self.runner.invoke(cli, ['--clear'], input='y')
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'basic',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/basic.zip',
            Path('basic.py').resolve().__str__()
        )

    def test_basic_dir(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_dir'))
        self.runner.invoke(cli, ['--name', 'basic_dir'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'basic_dir',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/basic_dir.zip',
            Path('basic_dir').resolve().__str__()
        )

    def test_basic_dir_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_dir'))
        self.runner.invoke(cli, ['--clear'], input='y')
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'basic_dir',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/basic_dir.zip',
            Path('basic_dir').resolve().__str__()
        )

    def test_basic_multiple(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_multiple'))
        self.runner.invoke(cli, ['--name', 'fn_one'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'fn_one',
            Path('fn_one.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/fn_one.zip',
            Path('fn_one.py').resolve().__str__()
        )

    def test_basic_multiple_fn_two(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_multiple'))
        self.runner.invoke(cli, ['--name', 'fn_two'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'fn_two',
            Path('fn_two.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/fn_two.zip',
            Path('fn_two.py').resolve().__str__()
        )

    def test_basic_multiple_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'basic_multiple'))
        self.runner.invoke(cli, ['--clear'], input='y')
        self.runner.invoke(cli, ['-load'], input='1')        
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'fn_one',
            Path('fn_one.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/fn_one.zip',
            Path('fn_one.py').resolve().__str__()
        )       

    def test_module_basic(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_basic'))
        self.runner.invoke(cli, ['--name', 'mod_basic'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'mod_basic',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/mod_basic.zip',
            Path('mod_basic.py').resolve().__str__()
        )        

    def test_module_basic_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_basic'))
        self.runner.invoke(cli, ['--clear'], input='y')
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'mod_basic',
            Path('requirements.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/mod_basic.zip',
            Path('mod_basic.py').resolve().__str__()
        )

    def test_module_mult(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult'))
        self.runner.invoke(cli, ['--name', 'module_mult_one'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'module_mult_one',
            Path('module_mult_one.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/module_mult_one.zip',
            Path('module_mult_one.py').resolve().__str__()
        )

    def test_module_mult_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult'))
        self.runner.invoke(cli, ['--clear'], input='y')
        self.runner.invoke(cli, ['-load'], input='1')        
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'module_mult_one',
            Path('module_mult_one.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/module_mult_one.zip',
            Path('module_mult_one.py').resolve().__str__()
        )

    def test_module_mult_folder_dir(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))
        self.runner.invoke(cli, ['--name', 'module_mult_folder_dir'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'module_mult_folder_dir',
            Path('module_mult_folder_dir.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/module_mult_folder_dir.zip',
            Path('module_mult_folder_dir').resolve().__str__()
        )

    def test_module_mult_folder_file(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))
        self.runner.invoke(cli, ['--name', 'module_mult_folder_file'])
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'module_mult_folder_file',
            Path('module_mult_folder_file.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/module_mult_folder_file.zip',
            Path('module_mult_folder_file.py').resolve().__str__()
        )

    def test_module_mult_folder_no_name(self):
        os.chdir(self.file_dir.joinpath('tf_test', 'module_mult_folder'))
        self.runner.invoke(cli, ['--clear'], input='y')
        self.runner.invoke(cli, ['-load'], input='2')          
        config = ConfigLoader.add_defaults()
        self.check_config(
            config,
            'module_mult_folder_dir',
            Path('module_mult_folder_dir.txt').resolve().__str__(),
            'aws-lambda-project-code',
            'maniple/test/1.0.0/module_mult_folder_dir.zip',
            Path('module_mult_folder_dir').resolve().__str__()
        )

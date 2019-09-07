import time

from click.testing import CliRunner
from unittest import TestCase
from maniplecli.commands.config import cli
from maniplecli.util.config_loader import ConfigLoader


class TestConfigCommand(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def get_config(self):
        return ConfigLoader.load_config()

    # Test setting values
    def test_incorrect_tf_file(self):
        result = self.runner.invoke(cli, ['--tf-file', 'incFilename'])
        self.assertEquals(result.exit_code, 1)

    def test_set_s3_bucket(self):
        result = self.runner.invoke(cli, ['--s3-bucket', 's3-bucket-name'])
        self.assertEquals(result.exit_code, 0)
        self.assertEquals(self.get_config()['s3_bucket'], 's3-bucket-name')

    def test_set_lambda_name(self):
        result = self.runner.invoke(cli, ['--name', 'name'])
        self.assertEquals(result.exit_code, 0)
        self.assertEquals(self.get_config()['name'], 'name')

    # Test functionality
    def test_new_name_wipe_config(self):
        self.runner.invoke(cli, ['--s3-bucket', 'bucket'])
        config_ini = self.get_config()
        # Ensure there is something to wipe
        self.assertEquals(config_ini['s3_bucket'], 'bucket')
        result = self.runner.invoke(cli, ['--name', 'new_name'])
        config = self.get_config()
        self.assertEquals(result.exit_code, 0)
        self.assertEquals(config['name'], 'new_name')
        for key, items in config.items():
            if key not in ['name', 'tf_file','package']:
                self.assertEquals(config[key], None)

    def test_replace(self):
        with self.runner.isolated_filesystem():
            with open('wrongScript.py', 'w') as f:
                f.write('asdf')
            result = self.runner.invoke(cli, ['--s3-key', 'path/to/wrongName.zip',
                                              '--name', 'wrongName',
                                              '--script', 'wrongScript.py'])
            config = self.get_config()
            self.assertEquals(result.exit_code, 0)
            self.assertEquals(config['name'], 'wrongName')
            self.runner.invoke(cli, ['-rep', 'wrong', 'right'])
            config = self.get_config()
            self.assertEquals(config['name'], 'rightName')
            self.assertTrue('rightScript' in config['script'])

    def test_save(self):
        self.runner.invoke(cli, ['--name', 'manipleTestSave'])
        result = self.runner.invoke(cli, ['-save', 'manipleTestSave'])
        self.assertEquals(result.exit_code, 0)

    def test_open(self):
        self.runner.invoke(cli, ['--name', 'initiateConfigWipe'])
        self.runner.invoke(cli, ['-open', 'manipleTestSave'])
        time.sleep(1)
        config = self.get_config()
        self.assertEquals(config['name'], 'manipleTestSave')

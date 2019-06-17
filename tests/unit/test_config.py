import click
import json
import os

from click.testing import CliRunner
from pyfakefs import fake_filesystem_unittest
from unittest import TestCase
from mock import patch
from maniplecli.commands.config import cli
from pathlib import Path


class TestConfigCommand(TestCase):
    def setUp(self):
        self.runner = CliRunner()
        
    def test_incorrect_tf_file(self):
        result = self.runner.invoke(cli, ['--tf-file', 'incFilename'])
        self.assertEquals(result.exit_code, 1)

    def test_correct_tf_file(self):
        with self.runner.isolated_filesystem():
            with open("incFilename.tf", "w") as f:
                f.write("asdf")
            result = self.runner.invoke(cli, ['--tf-file', 'incFilename.tf'])
            self.assertEquals(result.exit_code, 0)    

    def test_set_s3_bucket(self):
        result = self.runner.invoke(cli, ['--s3-bucket', "s3-bucket-name"])
        self.assertEquals(result.exit_code, 0)
        self.assertEquals(self._config("s3_bucket"), "s3-bucket-name")

    def test_set_lambda_name(self):
        result = self.runner.invoke(cli, ['--lambda-name', "name"])
        self.assertEquals(result.exit_code, 0)
        self.assertEquals(self._config("lambda_name"), "name")
        path = os.path.join(os.path.dirname(__file__), "..", "..", "maniplecli", "deployment_packages", "name")
        self.assertEquals(self._config("package"), Path(path).resolve().__str__())

    def test_replace(self):
        with self.runner.isolated_filesystem():
            with open("wrongScript.py", "w") as f:
                f.write("asdf")
            result = self.runner.invoke(cli, ['--s3-key', 'path/to/wrongName.zip',
                                            '--lambda-name', 'wrongName',
                                            '--script', 'wrongScript.py'
                                        ])
            self.assertEquals(result.exit_code, 0)
            self.assertEquals(self._config("lambda_name"), 'wrongName')
            rep_result = self.runner.invoke(cli, ['-rep', 'wrong', 'right'])
            self.assertEquals(self._config("lambda_name"), 'rightName')
            self.assertTrue('rightScript' in self._config("script"))
        
    def _config(self, key):
        with open(os.path.join(os.path.dirname(__file__),"..", "..", "config.json"), "r") as f:
            config = json.load(f)
        return config[key]
    





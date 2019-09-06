import click
import os

from pathlib import Path


class pyapp:
    def __init__(self, name):
        self.name = name

    def run(self):
        try:
            self.write_py_main()
            Path('requirements.txt').touch()
            self.write_py_file()
            self.write_test_folder()
        except FileExistsError:
            click.echo('Already attempted to create a lambda function here.')
            click.echo('Delete files and try again.')
            return 1
        return 0

    def write_py_main(self):
        f = open('main.tf', 'w')
        f.write(self.main_tf_provider())
        f.write(self.main_tf_role())
        f.write(self.main_tf_version())
        f.write(self.main_tf_resource('python3.6'))
        f.close()

    def write_py_file(self):
        src = Path(Path.cwd(), 'src')
        src.mkdir()
        os.chdir(src)
        f = open('{}.py'.format(self.name), 'w')
        f.write(self.python_file_str())
        f.close()
        os.chdir('..')

    def write_test_folder(self):
        tests = Path(Path.cwd(), 'tests')
        tests.mkdir()
        os.chdir(tests)
        unit_dir = Path(Path.cwd(), 'unit')
        unit_dir.mkdir()
        os.chdir(unit_dir)
        f = open('test_handler.py', 'w')
        f.write(self.py_unit_test_str())
        f.close()
        os.chdir('../..')

    def main_tf_provider(self):
        return '''
provider "aws" {
  region = "us-east-1"
}\n
'''

    def main_tf_role(self):
        return '''
data "aws_iam_role" "{0}_role" {{
  name = "{0}_role"
}}
'''.format(self.name)

    def main_tf_version(self):
        return '''
variable "version" {
  type = "string"
  default = "1.0.0"
}\n
'''

    def main_tf_resource(self, runtime):
        return '''
resource "aws_lambda_function" "{n}" {{
  description = "<<description>>"
  function_name = "{n}"
  s3_bucket = "<<s3-bucket-name>>"
  s3_key = "<<s3-key-name>>"
  role = "${{data.aws_iam_role.{n}_role.arn}}"
  handler = "{n}.handler"
  runtime = "{r}"
  timeout = 1
  memory_size = 128
}}
'''.format(n=self.name, r=runtime)

    def python_file_str(self):
        return '''
def handler(event, context):
    print(event['target'])
    return 0
'''

    def py_unit_test_str(self):
        return '''
import importlib.util
from unittest import TestCase
from pathlib import Path


class TestHandler(TestCase):
    """Loads module without __init__"""
    def setUp(self):
        file_to_test = '{name}.py'
        path = Path(__file__, '..', '..', '..', 'src', file_to_test)
        print(path)
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location(
            file_to_test,
            path
        )
        self.module = importlib.util.module_from_spec(spec)
        self.module.__spec__.loader.exec_module(self.module)

    def test_handler_returns_zero(self):
        event = {{'target': '1'}}
        context = 0
        result = self.module.handler(event, context)
        self.assertEqual(result, 0)
'''.format(name=self.name)

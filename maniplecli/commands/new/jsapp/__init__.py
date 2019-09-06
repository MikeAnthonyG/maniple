import click
import json
import os
import platform

from pathlib import Path

from maniplecli.util.shell import Shell


class jsapp:
    def __init__(self, name):
        self.name = name

    def run(self):
        try:
            self.write_js_main()
            self.write_package_json()
            self.write_js_file()
            self.write_test_folder()
            # Windows require .cmd to run npm
            if platform.system() == 'Windows':
                Shell.run('npm.cmd install', os.getcwd())
            else:
                Shell.run('npm install', os.getcwd())
        except FileExistsError:
            click.echo('Already attempted to create a lambda function here.')
            click.echo('Delete files and try again.')
            return 1
        return 0

    def write_js_main(self):
        f = open('main.tf', 'w')
        f.write(self.main_tf_provider())
        f.write(self.main_tf_role())
        f.write(self.main_tf_version())
        f.write(self.main_tf_resource('nodejs8.10'))
        f.close()

    def write_package_json(self):
        with open('package.json', 'w') as f:
            json.dump(
                self.package_json_dict(),
                f,
                indent=2
            )

    def write_js_file(self):
        src = Path(Path.cwd(), 'src')
        src.mkdir()
        os.chdir(src)
        f = open('{}.js'.format(self.name), 'w')
        f.write(self.js_file_str())
        f.close()
        os.chdir('..')

    def write_test_folder(self):
        tests = Path(Path.cwd(), 'tests')
        tests.mkdir()
        os.chdir(tests)
        unit_dir = Path(Path.cwd(), 'unit')
        unit_dir.mkdir()
        os.chdir(unit_dir)
        f = open('test-handler.js', 'w')
        f.write(self.js_unit_test_str())
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

    def js_file_str(self):
        return '''
exports.handler = function (event, context) {
    return 'hello world';
};
'''

    def js_unit_test_str(self):
        return '''
'use strict';

const app = require('../../src/{name}.js');
const chai = require('chai')
const expect = chai.expect;
var event, context;

describe('Tests return hello world', function() {{
    it('verifies successful response', () => {{
        const result = app.handler(event, context);
        expect(result).to.be.equal('hello world');
    }});
}})
'''.format(name=self.name)

    def package_json_dict(self):
        return {
            'name': self.name,
            'version': '1.0.0',
            'main': './src/{}.js'.format(self.name),
            'scripts': {
                'test': 'mocha tests/unit/'
            },
            'devDependencies': {
                'chai': '^4.2.0',
                'mocha': '^6.2.0'
            }
        }

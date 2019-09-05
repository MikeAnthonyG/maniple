import os

from pathlib import Path

class jsapp:
    def __init__(self, name):
        self.name = name

    def run(self):
        self.write_js_main()
        Path('package.json').touch()
        self.write_js_file()
        self.write_test_folder()
        return 0


    def write_js_main(self):
        f = open('main.tf', 'w')
        f.write(self.main_tf_provider())
        f.write(self.main_tf_role())
        f.write(self.main_tf_version())
        f.write(self.main_tf_resource('nodejs8.10'))
        f.close()


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
        f.write(self.write_js_unit_test())
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
  role = "${{data.aws_iam_role.{n}.arn}}"
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

    def write_js_unit_test(self):
        return '''
'use strict';

const app = require('../../src/{name}.js');
const chai = require('chai')
const expect = chai.expect;
var event, context;

describe('Tests return hello world', function() {{
    const result = app.handler(event, context);
    expect(result).to.be.equal('hello world');
}})
'''.format(name=self.name)

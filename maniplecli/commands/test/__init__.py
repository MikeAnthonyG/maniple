import click
import logging
import os
import sys
import platform

from pathlib import Path

from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HELP_TEXT = '''
Run tests in the lambda function directory.

    maniple test [TEST_NAME]

Run all tests:
$ maniple test\n
\n
Run a single test file:
$ maniple test -f test_handler.py
'''

@click.command('test', help=HELP_TEXT, short_help='Run tests')
@click.option('-f', '--filename', help='Run a single test file.',
                 default=None)
def cli(filename):
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())

    if 'python' in ConfigLoader.get_runtime(config):
        run_py_tests(config, filename)
    elif 'nodejs' in ConfigLoader.get_runtime(config):
        run_js_tests(config, filename)


def run_py_tests(config, test_file):
    if not Path('./tests').exists():
        click.echo('No \'tests\' or \'test\' folder exists.')
        sys.exit(1)

    if test_file is not None:
        test_path = Path('./tests', test_file)
        if not test_path.exists():
            click.echo('No file found.')
            sys.exit(1)
        os.chdir(test_path.parent)
        run_test('python -m unittest {}'.format(test_path.name), 'python')
        sys.exit(0)

    tests_to_run = get_test_files('./tests', [])
    for t in tests_to_run:
        os.chdir(t.parent)
        run_test('python -m unittest {}'.format(t.name), 'python')
    

def run_js_tests(config, test_file):
    if not Path('./tests').exists():
        click.echo('No \'tests\' or \'test\' folder exists.')
        sys.exit(1)        

    if test_file is not None:
        click.echo('Single file tests not supported for nodejs yet.')
        click.echo('Change package.json values to perform individual tests.')
        sys.exit(0)

    # Windows requires .cmd to be added to the command to work
    if platform.system() == 'Windows':
        run_test('npm.cmd test', 'nodejs')
    else:
        run_test('npm test', 'nodejs')
    

def get_test_files(dir_, test_list):
    for f in Path(dir_).iterdir():
        if Path(f).is_dir():
            get_test_files(f, test_list)
        else:
            if 'test' == f.name[:4] and (f.suffix == '.py' or f.suffix == '.js'):
                test_list.append(Path(f))
    return test_list


def run_test(cmd, runtime):
    return_code, out, err = Shell.run(cmd, os.getcwd())
    if return_code == 0:
        if runtime == 'nodejs':
            click.echo(out)
        else:
            click.echo(out)  # Prints vars from print() statements
            click.echo(err)  # Prints results of unit test
        logger.debug(out)
    else:
        click.secho('{} failed.'.format(cmd), fg='red')
        logger.debug(err)
        sys.exit(1)

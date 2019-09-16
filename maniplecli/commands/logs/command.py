import click
import logging
import os
import sys

from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HELP_TEXT = """
Under construction
Invoke SAM patterns. 

\n
Watch the logs of a function.
$ maniple sam -w \n
\b
"""


@click.command('sam',
               help=HELP_TEXT, short_help='Invoke user defined SAM patterns')
@click.option('-w', '--watch',
              help='Watch the logs of a function.', is_flag=True)
@click.option('-e', '--error-logs',
              help='Watch the error logs of a function.', is_flag=True)
@click.option('-l', '--lambda_name',
              help='Lambda name to view logs - defaults to config', default=None)
def cli(watch, error_logs, lambda_name):
    run_cli(watch, error_logs, lambda_name)


def run_cli(watch, error_logs, lambda_name):
    if lambda_name is None:
        config = ConfigLoader.add_defaults(ConfigLoader.load_config())
        lambda_name = config['name']
    if watch:
        _watch(lambda_name)
    if error_logs:
        _error(lambda_name)
    sys.exit(0)


def _watch(lambda_name):
    cmd = ['sam', 'logs', '-n', lambda_name, '--tail']
    return_code, out, err = Shell.run(cmd, os.getcwd())
    if return_code == 0:
        logger.debug(out)
        sys.exit(0)
    else:
        logger.debug(err)
        sys.exit(1)


def _error(lambda_name):
    cmd = [
        'sam', 'logs', '-n',
        lambda_name, '--tail',
        '--filter', '\"error\"'
    ]
    return_code, out, err = Shell.run(cmd, os.getcwd())
    if return_code == 0:
        logger.debug(out)
        sys.exit(0)
    else:
        logger.debug(err)
        sys.exit(1)

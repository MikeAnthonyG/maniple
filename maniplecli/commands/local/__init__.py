import logging
import click
import json
import sys

from pathlib import Path, PurePath

from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell
from maniplecli.util.tf_converter import TerraformConverter
from maniplecli.commands.pack.command import _create_package

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HELP_TEXT = """
Help text here.
"""


@click.command('local', help=HELP_TEXT, short_help='Test locally.')
@click.option('-t', '--test', help='', is_flag=True, default=True)
def cli(test):
    run_cli(test)


def run_cli(test):
    if test:
        _test()
    sys.exit(0)


def _test():
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())
    tc = TerraformConverter()
    test_dir = Path(Path.cwd(), 'test_' + config['name'])
    logger.debug(test_dir)
    if test_dir.exists() is False:
        click.confirm('No test directory exists. Create test directory?',
                      abort=True)
        try:
            test_dir.mkdir(parents=False)
        except FileNotFoundError as e:
            logger.debug(e)
            click.echo('Incorrect directory for testing.')
            sys.exit(1)
    cf = tc.to_cloudformation(config)
    # Save cloudformation as SAM template
    save_json(
        PurePath.joinpath(test_dir, 'sam_template.json'),
        cf
    )
    logger.debug(cf)
    sys.exit(0)
    if bool(cf['Properties']['Environment']):
        # Save formatted env vars to test dir
        save_json(
            PurePath.joinpath(test_dir, 'env_vars.json'),
            convert_env_vars(
                cf['Properties']['Environment'],
                config
            )
        )

    events = [x for x in test_dir.iterdir()
              if 'event' in x.name and x.suffix == '.json']
    if len(events) == 0:
        logger.debug('No events in {}'.format(test_dir.name))
        click.echo('No events in {}. Shutting down.'.format(
            test_dir.name
        ))
        sys.exit(1)

    # Set environmental vars for SAM
    if bool(cf['Properties']['Environment']):
        return_code, out, err = Shell.run(
            'sam local invoke --env-vars {}'.format(Path(test_dir,
                                                         'env_vars.json')),
            Path.cwd()
        )
        if return_code == 0:
            logger.debug(out)
        else:
            logger.debug(err)
            click.echo('Failed to set environmental variables.')
            sys.exit(1)

    # Create deployment package 
    _create_package(
        config['script'],
        config['requirements'],
        config['package']
    ) 

    for event in events:
        cmd = 'sam local invoke \"{}\" -e {}'.format(
            config['name'],
            event.resolve()
        )
        return_code, out, err = Shell.run(
            cmd,
            Path.cwd()
        )
        if return_code == 0:
            logger.debug(out)
        else:
            logger.debug(err)
            click.echo('Failed to invoke function with event {}.'.format(
                event.resolve()
            ))
            sys.exit(1)


def convert_env_vars(env_vars, config):
    return {config['name']: env_vars['variables']}


def save_json(file_location, dict_):
    logger.debug('Saving to file {} \n{}'.format(
        file_location, dict_
    ))
    with open(file_location, 'w') as f:
        json.dump(dict_, f, indent=4)

import click
import hcl
import json
import logging
import os
import shutil
import sys

from pathlib import Path

from maniplecli.commands.pack.command import (_create_package, _update_script,
                                              _upload_package, _update_function)
from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


HELP_TEXT = """
    Deploys your function by creating a package, uploading it, and notifying 
    AWS.

    \n\b
    Deploy your function
    $ maniple deploy \n
    \b
    Deploys all functions in your main.tf file.
    $ maniple deploy -a \n
    \b
    Deploy all functions and run terraform apply
    $ maniple deploy -a -n \n
    \b
    Only updates the script of the function and deploys it.
    $ maniple deploy -u \n
    \b
    Deploy lambda and use terraform to create the resource (run terraform apply)
    $ maniple deploy -n    
"""


@click.command('deploy', help=HELP_TEXT, short_help='Deploy Lambda functions.')
@click.option('-a', '--all',
              help='Deploys all Lambda resources in a terraform file',
              is_flag=True, default=False)
@click.option('-u', '--update',
              help='Deploys the function with an updated script.',
              is_flag=True, default=False)
@click.option('-n', '--new-function',
              help='Deploys a new AWS resource with Terraform Apply',
              is_flag=True, default=False)
def cli(all, update, new_function):
    run_cli(all, update, new_function)


def run_cli(all, update, new_function):
    config = ConfigLoader.load_config()
    if all:
        _deploy_all(new_function)
    else:
        if update:
            _update(config)
        elif new_function:
            _new_function(config)
        else:
            _deploy(config)
    sys.exit(0)


def _deploy(config):
    _create_package(config['script'], config['requirements'], config['package'])
    _upload_package(config['s3_bucket'], config['s3_key'], config['package'])
    _update_function(config['name'], config['s3_bucket'], config['s3_key'])


def _update(config):
    _update_script(config['package'], config['script'])
    _upload_package(config['s3_bucket'], config['s3_key'], config['package'])
    _update_function(config['name'], config['s3_bucket'], config['s3_key'])


def _new_function(config):
    _create_package(config['script'], config['requirements'], config['package'])
    _upload_package(config['s3_bucket'], config['s3_key'], config['package'])

    terraform_commands = ['terraform init', 'terraform apply -auto-approve']
    for cmd in terraform_commands:
        return_code, out, err = Shell.run(cmd, os.getcwd())
        if return_code == 0:
            click.secho('{} ran successfully.'.format(cmd), fg='green')
            logger.debug(out)
        else:
            click.secho('{} failed.'.format(cmd), fg='red')
            logger.debug(err)
            sys.exit(1)


def _deploy_all(apply_flag=False):
    config = ConfigLoader.load_config()
    resources_to_deploy = ConfigLoader.get_possible_resources(
        ConfigLoader.load_terraform(config['tf_file'])
    )
    logger.debug('Resources to deploy: {}'.format(
        resources_to_deploy
    ))
    for resource in resources_to_deploy:
        # resource = (int_value, name, resource_or_module)
        temp_config = ConfigLoader.reset_config()
        temp_config['name'] = resource[1]
        temp_config = ConfigLoader.add_defaults(temp_config)
        _create_package(
            temp_config['script'],
            temp_config['requirements'],
            temp_config['package'])
        _upload_package(
            temp_config['s3_bucket'],
            temp_config['s3_key'],
            temp_config['package'])
        logger.debug('Created and uploaded {} resource'.format(temp_config['name']))
        if apply_flag is False:
            _update_function(
                temp_config['name'],
                temp_config['s3_bucket'],
                temp_config['s3_key'])

    if apply_flag:
        terraform_commands = ['terraform init', 'terraform apply -auto-approve']
        for cmd in terraform_commands:
            return_code, out, err = Shell.run(cmd, os.getcwd())
            if return_code == 0:
                click.secho('{} ran successfully.'.format(cmd), fg='green')
                logger.debug(out)
            else:
                click.secho('{} failed.'.format(cmd), fg='red')
                logger.debug(err)
                sys.exit(1)

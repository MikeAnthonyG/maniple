import logging
import click
import os
import sys

from maniplecli.commands.pack.command import (create_package_fn,
                                              update_script_fn,
                                              upload_package_fn,
                                              update_function_fn)
from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    Deploy lambda and use terraform to create the resource (ie run terraform apply)
    $ maniple deploy -n \n
    \b
    Deploy all lambda resources in a file with user terraform file name (defaults to 'main.tf')
    $ maniple deploy -a -n -t my_resources.tf
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
@click.option('-m', '--main_tf_file',
              help='Name of terraform file (Default=main.tf) for use with .tf.json files',
              default='main.tf')
@click.option('-t', '--target',
              help='Target terraform resource, must be in form of resource.aws_lambda_function.name',
              default=None)
def cli(all, update, new_function, main_tf_file, target):
    run_cli(all, update, new_function, main_tf_file, target)


def run_cli(all, update, new_function, main_tf_file, target):
    if all:
        _deploy_all(new_function, main_tf_file)
    else:
        if update:
            _update()
        elif new_function:
            _new_function(target)
        else:
            _deploy()
    sys.exit(0)


def _deploy():
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())
    create_package_fn(config['script'], config['requirements'], config['package'])
    upload_package_fn(config['s3_bucket'], config['s3_key'], config['package'])
    update_function_fn(config['name'], config['s3_bucket'], config['s3_key'])


def _update():
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())
    update_script_fn(config['package'], config['script'])
    upload_package_fn(config['s3_bucket'], config['s3_key'], config['package'])
    update_function_fn(config['name'], config['s3_bucket'], config['s3_key'])


def _new_function(target):
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())
    create_package_fn(config['script'], config['requirements'], config['package'])
    upload_package_fn(config['s3_bucket'], config['s3_key'], config['package'])
    _terraform_apply(target)


def _deploy_all(apply_flag, tf_file):

    resources_to_deploy = ConfigLoader.get_possible_resources(
        ConfigLoader.load_terraform(tf_file)
    )
    logger.debug('Resources to deploy: {}'.format(
        resources_to_deploy
    ))
    for resource in resources_to_deploy:
        # resource = (int_value, name, resource_or_module)
        temp_config = ConfigLoader.reset_config()
        temp_config['name'] = resource[1]
        temp_config = ConfigLoader.add_defaults(temp_config)
        create_package_fn(
            temp_config['script'],
            temp_config['requirements'],
            temp_config['package'])
        upload_package_fn(
            temp_config['s3_bucket'],
            temp_config['s3_key'],
            temp_config['package'])
        logger.debug('Created and uploaded {} resource'.format(temp_config['name']))
        if apply_flag is False:
            update_function_fn(
                temp_config['name'],
                temp_config['s3_bucket'],
                temp_config['s3_key'])

    if apply_flag:
        _terraform_apply(None)


def _terraform_apply(target):
    logger.debug('Target: {}'.format(target))
    if target is not None:
        terraform_commands = [
            'terraform init',
            'terraform apply -target={} -auto-approve'.format(target)
        ]
    else:
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

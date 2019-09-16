import boto3
import click
import logging
import os
import shutil
import sys
import zipfile

from maniplecli.util.lambda_packages import lambda_packages

from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.package_downloader import PackageDownloader
from pathlib import Path
from zipfile import ZipFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HELP_TEXT = """
Use this command to zip site-packages, update deployment packages with new code, create deployment packages, send to s3\n

Setting up the config file with "maniple config" will save time re-entering parameters.

Once the config file is set up, these commands can be used to quick pack and upload your function.
\n\b
Zip the necesary packages and python script into a deployment package located where the package variable is set.
$ maniple pack -c \n
\b
Create a deployment package and upload the file to s3
$ maniple pack -c -up \n
\b 
Create a deployment package, upload it, and notify AWS that the lambda function has been updated.
$ maniple pack -c -up -uf \n
\b
Update the python script in your deployment function, upload it, update the function, and invoke it.
$ maniple pack -us -up -uf -i\n
\b
Upload a zipped deployment package with only the python script included. Set the requirements parameter
to None and then use --update-script and --upload-package
$ maniple config -r None
$ maniple pack -us -up
"""


def list_libraries(ctx, param, value):
    if value is False:
        return

    _str = ''
    for key, value in lambda_packages.items():
        _str = _str + 'Name: {} \nVersions: {}\n'.format(key, list(value.keys()))
    click.echo_via_pager(_str)
    ctx.exit()


@click.command('pack', help=HELP_TEXT,
               short_help='Zip your virtual environments and send to s3')
@click.option('-c', '--create-package',
              help='Creates deployment package', is_flag=True)
@click.option('-i', '--invoke',
              help='Invokes lambda', is_flag=True)
@click.option('-us', '--update-script',
              help='Updates script in package', is_flag=True)
@click.option('-uf', '--update-function',
              help='Notify AWS that the function was updated.', is_flag=True)
@click.option('-up', '--upload-package',
              help='Uploads package to s3', is_flag=True)
@click.option('-libs', '--libraries',
              help='List libraries that can be replaced.', is_flag=True,
              is_eager=True, callback=list_libraries, default=False)
def cli(create_package, invoke, update_script, update_function, libraries,
        upload_package):
    run_cli(create_package, invoke, update_script, update_function, libraries,
            upload_package)


def run_cli(create_package, invoke, update_script, update_function, libraries,
            upload_package):
    config = ConfigLoader.add_defaults(ConfigLoader.load_config())

    if update_script:
        update_script_fn(config['package'], config['script'])
    if create_package:
        create_package_fn(config['script'],
                          config['requirements'],
                          config['package'])
    if upload_package:
        click.echo('Uploading file to s3 bucket...')
        upload_package_fn(config['s3_bucket'],
                          config['s3_key'],
                          config['package'])
    if update_function:
        click.echo('Updating function on AWS...')
        click.echo(update_function_fn(config['name'],
                                      config['s3_bucket'],
                                      config['s3_key']))
    if invoke:
        click.echo('Invoking lambda...')
        _invoke(config['name'])

    sys.exit(0)


def create_package_fn(script, requirements, package):
    """
    Creates a zipped package with all libraries and scripts necesary to run
    the function on AWS.

    Args:
        script: file or dir that holds the main script/s of the function
        requirements: location of the requirements file
        package: file location of where the deployment package 
    """
    try:
        logger.debug('Attempting to make package dir at {}'.format(package))
        os.makedirs(package)
        logger.debug('Made package dir at {}'.format(package))
    except FileExistsError:
        shutil.rmtree(package)
        os.makedirs(package)
        logger.debug('Deleted previous dir and made a new one'.format(package))

    PackageDownloader.download_packages(script, requirements, package)

    _zip_files()
    click.secho('Package created.', fg='green')


def update_script_fn(package, script):
    """
    Updates only the user created code of a function

    Args:
        script: file or dir that holds the main script/s of the function
        package: file location of where the deployment package 
    """    
    _zip_files()
    click.secho('Script updated.', fg='green')


def upload_package_fn(s3_bucket, s3_key, package):
    """
    Creates a zipped package with all libraries and scripts necesary to run
    the function on AWS.

    Args:
        script: file or dir that holds the main script/s of the function
        requirements: location of the requirements file
        package: file location of where the deployment package 
    """
    try:
        s3 = boto3.resource('s3')
        s3.Bucket(s3_bucket).upload_file(
            os.path.join(package, '{}.zip'.format(package)),
            s3_key)
        click.secho('Upload successful.', fg='green')
    except Exception as e:
        click.secho('Upload failed: {}'.format(e), fg='red')


def update_function_fn(function_name, s3_bucket, s3_key):
    """
    Notifies AWS that the function code has been updated.

    Args:
        function_name: name of the function
        s3_bucket: s3_bucket that holds the deployment package
        s3_key: s3_key of the deployment package
    """
    client = boto3.client('lambda')
    try:
        response = client.update_function_code(FunctionName=function_name,
                                               S3Bucket=s3_bucket,
                                               S3Key=s3_key)
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            click.secho('Update function failed: {}'.format(
                response['ResponseMetadata']['HTTPStatusCode']), fg='red')
        else:
            click.secho('{} updated successfully'.format(function_name), fg='green')
    except client.exceptions.ResourceNotFoundError as e:
        click.secho(e, fg='red')


def _invoke(lambda_name):
    """
    Invokes the lambda function on the cloud.

    Args:
        lambda_name: name of the lambda function on AWS
    """
    client = boto3.client('lambda')
    try:
        response = client.invoke(FunctionName=lambda_name)
        click.echo('Function Response:')
        click.echo(response)
        click.echo('View more logs with: maniple sam -w')
    except client.exceptions.ResourceNotFoundError as e:
        click.secho(e, fg='red')


def _zip_files():
    """
    Zip all necesary files for the deployment package.
    """
    config = ConfigLoader.load_config()

    with ZipFile(os.path.join(config['package'], '{}.zip'.format(config['package'])), 'w',
                 zipfile.ZIP_DEFLATED) as zip:
        # Zip packages from requirements
        for dirname, subdirs, files in os.walk(config['package']):
            for filename in files:
                abs_name = os.path.abspath(os.path.join(dirname, filename))
                arc_name = abs_name[len(config['package']) + 1:]
                logger.debug('Zipped {} : {}'.format(abs_name, arc_name))
                zip.write(abs_name, arc_name)

        script = Path(config['script'])
        if script.is_dir():
            for dirname, subdirs, files in os.walk(config['script']):
                for filename in files:
                    abs_name = os.path.abspath(os.path.join(dirname, filename))
                    arc_name = abs_name[len(config['script']) + 1:]
                    logger.debug('Zipped {} : {}'.format(abs_name, arc_name))
                    zip.write(abs_name, arc_name)
        else:
            zip.write(config['script'], script.name)

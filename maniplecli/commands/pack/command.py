import boto3
import click
import hcl
import logging
import json
import os
import platform
import shutil
import subprocess
import sys
import re
import zipfile

from maniplecli.util.lambda_packages import lambda_packages
from maniplecli.util.config_loader import ConfigLoader
from pathlib import Path
from subprocess import PIPE
from subprocess import Popen
from zipfile import ZipFile


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

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'r') as f:
    CONFIG = json.load(f)

def list_libraries(ctx, param, value):
    if value is False:
        return

    _str = ''
    for key,value in lambda_packages.items():
        _str = _str + "Name: {} \nVersions: {}\n".format(key, list(value.keys()))
    click.echo_via_pager(_str)
    ctx.exit()
        

@click.command("pack",help=HELP_TEXT, short_help="Zip your virtual environments and send to s3")
@click.option("-c", "--create-package", help="Creates deployment package", is_flag=True)
@click.option('-i', "--invoke", help="Invokes lambda", is_flag=True)
@click.option("-us", "--update-script", help="Updates script in package", is_flag=True)
@click.option("-uf", "--update-function", help="Notify AWS that the function was updated.", is_flag = True)               
@click.option("-up", "--upload-package", help="Uploads package to s3", is_flag=True)
@click.option("-libs", "--libraries", help="List libraries that can be replaced.", is_flag=True, is_eager=True, callback=list_libraries, default=False)
def cli(create_package, invoke, update_script, update_function, libraries, upload_package):
    run_cli(create_package, invoke, update_script, update_function, libraries, upload_package)
    
def run_cli(create_package, invoke, update_script, update_function, libraries, upload_package):
    
    global CONFIG  
    CONFIG = ConfigLoader.add_defaults(CONFIG)

    if update_script:
        if CONFIG['requirements'] is not None:
            _update_script(CONFIG['package'], CONFIG['script']) 
        else:
            with ZipFile(CONFIG['package'], 'w', zipfile.ZIP_DEFLATED) as zip:
                script = CONFIG['script']
                if platform.system() == 'Windows':
                    zip.write(script, script.split("\\")[-1])    
                else:
                    zip.write(script, script.split("/")[-1])  
    if create_package:
        _create_package(CONFIG['script'], CONFIG['requirements'], CONFIG['package'])
    if upload_package:
        click.echo("Uploading file to s3 bucket...")
        _upload_package(CONFIG['s3_bucket'], CONFIG['s3_key'], CONFIG['package'])
    if update_function:
        click.echo("Updating function on AWS...")
        click.echo(_update_function(CONFIG['lambda_name'], CONFIG['s3_bucket'], CONFIG['s3_key']))      
    if invoke:
        click.echo("Invoking lambda...")
        _invoke(CONFIG['lambda_name'])

    sys.exit(0)
    
def _create_package(script, requirements, package):
    if requirements == None:
        raise TypeError("Config not set or requirements file not in folder: requirements, package")
    try:
        os.makedirs(CONFIG['package'])
    except FileExistsError:
        shutil.rmtree(CONFIG['package'])
        os.makedirs(CONFIG['package'])

    if "requirements.txt" in requirements:
        subprocess.call([
            'pip',
            'install',
            '--target={}'.format(package),
            "-r",
            requirements
        ])
    elif "package.json" in requirements:
        with open(requirements, 'r') as f:
            dependencies = json.load(f)
        for key, value in dependencies['dependencies'].items():
            try:
                subprocess.call([
                    'npm',
                    '--prefix',
                    os.path.abspath(package),
                    'install',
                    key
                ], shell=True)
            except Exception as e:
                click.echo(e)
                sys.exit(1)
    else:
        if Path(requirements).is_file() == False:
            click.secho("Requirements file is incorrect. Should be requirements.txt or package.json")
            sys.exit(1)

    with ZipFile(os.path.join(package, "{}.zip".format(package)), 'w', zipfile.ZIP_DEFLATED) as zip:
        for dirname, subdirs, files in os.walk(package):
            for filename in files:
                abs_name = os.path.abspath(os.path.join(dirname, filename))
                arc_name = abs_name[len(package) + 1:]
                zip.write(abs_name, arc_name)
        if platform.system() == 'Windows':
            zip.write(script, script.split("\\")[-1])    
        else:
            zip.write(script, script.split("/")[-1])  
    click.secho("Package created.", fg="green")  

def _update_script(package, script):  
    
    with ZipFile(os.path.join(package, "{}.zip".format(package)), 'w', zipfile.ZIP_DEFLATED) as zip:
        for dirname, subdirs, files in os.walk(package):
            for filename in files:
                abs_name = os.path.abspath(os.path.join(dirname, filename))
                arc_name = abs_name[len(package) + 1:]
                zip.write(abs_name, arc_name)
        if platform.system() == 'Windows':
            zip.write(script, script.split("\\")[-1])    
        else:
            zip.write(script, script.split("/")[-1])  
    click.secho("Script updated.", fg="green")
    
def _upload_package(s3_bucket, s3_key, package):
    try:
        s3 = boto3.resource('s3')
        s3.Bucket(s3_bucket).upload_file(os.path.join(package, "{}.zip".format(package)), s3_key)
        click.secho("Upload successful.", fg="green")
    except Exception as e:
        click.secho("Upload failed: {}".format(e), fg="red")

def _update_function(function_name, s3_bucket, s3_key):
    client = boto3.client("lambda")
    try:
        response = client.update_function_code(FunctionName=function_name, 
            S3Bucket=s3_bucket, S3Key=s3_key)  
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            click.secho("Update function failed: {}".format(response['ResponseMetadata']['HTTPStatusCode']), fg="red")
        else:
            click.secho("{} updated successfully".format(function_name), fg="green")
    
    except client.exceptions.ResourceNotFoundError as e:
        click.secho(e, fg="red")

def _invoke(lambda_name):
    client = boto3.client("lambda")
    try:
        response = client.invoke(FunctionName=lambda_name)
        click.echo("Function Response:")
        click.echo(response)
        click.echo("View more logs with: maniple sam -w")
    except client.exceptions.ResourceNotFoundError as e:
        click.secho(e, fg="red")  

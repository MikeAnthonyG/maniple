import click
import hcl
import json 
import os
import shutil
import sys
import zipfile

from pathlib    import Path
from zipfile     import ZipFile

from maniplecli.commands.pack.command import _create_package, _update_script, _upload_package, _update_function

HELP_TEXT = '''
    Deploys your function by creating a package, uploading it, and notifying AWS.

    \n\b
    Deploy your function
    $ maniple deploy \n
    \b
    Deploys all functions in your main.tf file. All functions will have their packages made from requirements.txt or package.json
    $ maniple deploy -a

'''

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'r') as f:
    CONFIG = json.load(f)

@click.command("deploy", help=HELP_TEXT, short_help="Deploy Lambda functions.")
@click.option("-a", "--all", help="Deploys all Lambda resources in a terraform file", is_flag=True, default=False)
def cli(all):
    run_cli(all)

def run_cli(all):
    if all:
        _deploy_all()
    else:
        _add_defaults_to_config()
        _deploy()
    sys.exit(0)

def _deploy():
    _create_package(CONFIG['script'], CONFIG['requirements'], CONFIG['package'])
    _upload_package(CONFIG['s3_bucket'], CONFIG['s3_key'], CONFIG['package'])
    _update_function(CONFIG['lambda_name'], CONFIG['s3_bucket'], CONFIG['s3_key'])

def _deploy_all():
    global CONFIG
    path = Path(".")
    files = os.listdir(path)
    try:
        with open(CONFIG['tf_file'], 'r') as f:
            tf = hcl.load(f)
    except FileNotFoundError as e:
        click.secho("Main terraform not found!", fg="red")
    
    try:
        functions = tf['resource']['aws_lambda_function']
        for name, values in functions.items():
            handler = values['handler'].split('.')[0]
            if 'python' in values['runtime']:
                runtime = 'python'
            else:
                runtime = 'nodejs'
            lambda_name = values['function_name']
            package = Path(os.path.join(os.path.dirname(__file__), "..", "..", "deployment_packages", lambda_name))
            try:
                os.makedirs(package)
            except FileExistsError:
                shutil.rmtree(package)
                os.makedirs(package)
            package = package.resolve().__str__()
            try:
                s3_bucket = values['s3_bucket']
                s3_key    = values['s3_key']
            except KeyError as e:
                click.secho("No S3 bucket or keys found in main.tf", fg='red')
            for f in files:
                if ".py" in f and runtime == "python":
                    if handler == f[:-3]:
                        script = Path(f).resolve().__str__()
                        try:
                            requirements = Path("./requirements.txt").resolve().__str__()
                        except FileNotFoundError as e:
                            click.echo("No requirements.txt found.\nCancelling deploy", fg='red')
                            sys.exit(1)
                elif ".js" in f and runtime == 'nodejs':
                    if handler == f[:-3]:
                        script = Path(f).resolve().__str__()
                        try:
                            requirements = Path("./package.json").resolve().__str__()
                        except FileNotFoundError as e:
                            click.echo("No package.json found.\nCancelling deploy.", fg='red')
                            sys.exit(1)
                else:
                    continue

            _create_package(script, requirements, package)
            _upload_package(s3_bucket, s3_key, package)
            _update_function(lambda_name, s3_bucket, s3_key)           
    except KeyError as e:
        click.echo(e)
    click.secho("All functions uploaded.", fg='green')

def _add_defaults_to_config():
    global CONFIG
    try:
        with open(CONFIG['tf_file'], 'r') as f:
            tf = hcl.load(f)
        runtime = tf['resource']['aws_lambda_function'][CONFIG['lambda_name']]['runtime']
        handler = tf['resource']['aws_lambda_function'][CONFIG['lambda_name']]['handler'].split('.')[0]
    except FileNotFoundError as e:
        click.secho("Main terraform not found!", fg="red")
    path = Path(".")
    files = os.listdir(path) 
    for f in files:
        if CONFIG['script'] == None:
            if f[-2:] == 'js' and 'nodejs' in runtime and handler == f[:-3]:
                CONFIG['script'] = Path(f).resolve().__str__()
            if f[-2:] == 'py' and 'python' in runtime and handler == f[:-3]:
                CONFIG['script'] = Path(f).resolve().__str__()
        if f == 'requirements.txt' and CONFIG['requirements'] == None and 'python' in runtime:
            CONFIG['requirements'] = Path(f).resolve().__str__()
        if f == 'package.json' and CONFIG['requirements'] == None and 'nodejs' in runtime:
            CONFIG['requirements'] = Path(f).resolve().__str__()
        if f == CONFIG['tf_file']:
            try:
                if CONFIG['s3_bucket'] == None:
                    CONFIG['s3_bucket'] = tf['resource']['aws_lambda_function'][CONFIG['lambda_name']]['s3_bucket']
                if CONFIG['s3_key'] == None:
                    CONFIG['s3_key'] = tf['resource']['aws_lambda_function'][CONFIG['lambda_name']]['s3_key']
            except KeyError as e:
                click.echo("Lambda name is not set or doesn't match the terraform file.")
                sys.exit(1)
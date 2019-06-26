import click
import hcl
import json 
import os
import shutil
import sys
import re
import zipfile

from pathlib    import Path
from zipfile     import ZipFile

from maniplecli.util.config_loader import ConfigLoader

HELP_TEXT = '''
This will set up the correct filepaths for working with terraform so that they don't need to be re-entered each time. \n
\b
Set up the location of the terraform file you want to work with. Defaults to "main.tf"
$ maniple config -t ./main.tf \n
\b
Set up s3 bucket.
$ maniple config -s3 "s3://lambda-code" \n
\b
Set up s3 key
$ maniple config -k "path/to/package.zip" \n
\b
Set current Lambda function name (This will reset your config file.)
$ maniple config -l "lambda_name" \n
\b
Point to your python requirements text file.
$ maniple config -r ../../requirements.txt\n
\b
Location of the python script to bundle with libraries or zip and upload to s3
$ maniple config -s ./script.py\n
\b
Location to save the zip package
$ maniple config -pkg . \n 
\b
Completely clear the config file.
$ maniple config -c \n
\b
Get your current config settings.
$ maniple config -g \n
\b
Reset value (such as the lambda s3 key value)
$ maniple config --s3-key None
\b
Save config
$ maniple config -save nameConfigHere
\b 
Open saved config
$ maniple config -open namedConfigHere
\b
List saved config files
$ maniple config -S 
\b
Load a config from directory 
$ maniple config -load
'''

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'r') as f:
    CONFIG = json.load(f)

def get_config(ctx, param, value):
    if value is False:
        return

    for key, value in CONFIG.items():
        if key == "package":
            continue
        elif value is not None:
            click.echo("{}{}: {}".format(click.style(key,fg="green"), (13-len(key))*" ", value))
        else:
            click.echo("{}{}: {}".format(click.style(key,fg="red"), (13-len(key))*" ", value))
    ctx.exit()

def clear_config(ctx, param, value):
    if value is False:
        return

    click.confirm('Are you sure you want to clear your configuration?', abort=True)

    for key, value in CONFIG.items():
        if key == "tf_file":
            CONFIG[key] = "main.tf"
        else:
            CONFIG[key] = None

    with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'w') as f:
        json.dump(CONFIG, f, indent=2, sort_keys=True)
    ctx.exit()

def get_saved_configs(ctx, param, value):
    if value is False:
        return

    _path = os.path.join(os.path.dirname(__file__), "..", "..", "util", "config_files")
    click.echo('\t'.join(sorted([x[:-5] for x in os.listdir(_path)])))
    ctx.exit()
    

@click.command("config", help=HELP_TEXT, short_help="Setup directories and functions for QoL.")
@click.option("-g", "--get", help="Get current config", is_flag=True, callback=get_config, is_eager=True)
@click.option("-c", "--clear", help="Clear current config", is_flag=True, callback=clear_config, is_eager=True)
@click.option("-S", "--see", help="List saved configs.", is_flag=True, callback=get_saved_configs, is_eager=True)
@click.option("-t", "--tf-file", help="TF file, defaults to main.tf",default=None)
@click.option("-s3", "--s3-bucket", help="Set s3 bucket", default=None)
@click.option("-k", "--s3-key", help="Set s3 key", default=None)
@click.option("-l", "--lambda-name", help="Set lambda function name", default=None)
@click.option("-r", "--requirements", help="Requirements for your package", default=None)
@click.option("-s", "--script", help="Script file location", default=None)
@click.option("-pkg", "--package", help="Zipped package to deploy. Defaults to your lambda name.", default=None)
@click.option("-rep", "--replace", help="Replace all instances of a string", nargs=2, required=False, default=None)
@click.option("-save", help="Save config file.", nargs=1, type=str, default=None)
@click.option("-open", 'open_', help="Open config file.", nargs=1, type=str, default=None)
@click.option("-load", help="Loads the config from the current directory's contents", is_flag=True, default=False)
def cli(tf_file, s3_bucket, s3_key, lambda_name, get, clear, requirements, script, package, replace,
        save, open_, see, load):
    
    global CONFIG

    if lambda_name is not None:
        for key, value in CONFIG.items():
            if key == "tf_file":
                CONFIG[key] = "main.tf"
            else:
                CONFIG[key] = None

    run_file_options(
        tf_file       = tf_file, 
        s3_bucket     = s3_bucket,
        s3_key        = s3_key, 
        lambda_name   = lambda_name,
        requirements  = requirements,
        script        = script,
        package       = package
    )
    
    run_general_options(get, clear, replace, save, open_, load) 

    sys.exit(0)

def run_file_options(**kwargs):
    '''
    Sets various config parameters.
    '''
    global CONFIG

    for option, filepath in kwargs.items():
        if option in ['s3_bucket', 's3_key', 'lambda_name'] and filepath != None:
            if option == 'lambda_name':
                _package_dir = Path(os.path.join(os.path.dirname(__file__), "..", "..", "deployment_packages", filepath))
                try:
                    os.makedirs(_package_dir)
                except FileExistsError:
                    shutil.rmtree(_package_dir)
                    os.makedirs(_package_dir)
                CONFIG['package'] = _package_dir.resolve().__str__()
                CONFIG['lambda_name'] = filepath
            else:
                CONFIG[option] = filepath
            continue

        if filepath is not None and filepath !='main.tf':
            _filepath = Path(filepath)
            if _filepath.is_file() or _filepath.is_dir():
                CONFIG[option] = _filepath.resolve().__str__()
            else:
                click.secho("Improper file name or file doesn't exist.", fg="red")   
                sys.exit(1)

    with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'w') as f:
            json.dump(CONFIG, f, indent=2, sort_keys=True)


def run_general_options(get, clear, replace, save, open_, load):
    '''
    Runs config options not related to setting config options
    '''
    global CONFIG

    if replace != ():
        for key, value in CONFIG.items():
            if value is not None:
                CONFIG[key] = value.replace(replace[0], replace[1])
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'w') as f:
            json.dump(CONFIG, f, indent=2, sort_keys=True)                

    if open_ is not None:
        try:
            _path = Path(os.path.join(os.path.dirname(__file__), "..", "..", "util", "config_files", open_ + '.json'))
            with open(_path, 'r') as f:
                CONFIG = json.load(f)
            with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'w') as f:
                json.dump(CONFIG, f, indent=2, sort_keys=True)
        except IOError as e:
            click.secho(e, fg="red")
            sys.exit(1)
        except:
            click.echo(sys.exc_info()[0])
            raise

    if save is not None:
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "util", "config_files", save + ".json"), 'w') as f:
            json.dump(CONFIG, f, indent=2, sort_keys=True)

    if load:
        CONFIG = ConfigLoader.add_defaults(CONFIG)
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'w') as f:
            json.dump(CONFIG, f, indent=2, sort_keys=True)
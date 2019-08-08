import click
import json
import os
import shutil
import sys

from pathlib import Path

from maniplecli.util.config_loader import ConfigLoader

HELP_TEXT = """
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
"""


def get_config(ctx, param, value):
    if value is False:
        return

    config = ConfigLoader.load_config()
    for key, value in config.items():
        if key == 'package':
            continue
        elif value is not None:
            click.echo('{}{}: {}'.format(click.style(key, fg='green'),
                                         (13-len(key))*' ', value))
        else:
            click.echo('{}{}: {}'.format(click.style(key, fg='red'),
                                         (13-len(key))*' ', value))
    ctx.exit()


def clear_config(ctx, param, value):
    if value is False:
        return

    click.confirm('Are you sure you want to clear your configuration?',
                  abort=True)

    config = ConfigLoader.load_config()
    for key, value in config.items():
        if key == 'tf_file':
            config[key] = 'main.tf'
        else:
            config[key] = None

    ConfigLoader.save_config(config)
    ctx.exit()


def get_saved_configs(ctx, param, value):
    if value is False:
        return

    path = os.path.join(
        os.path.dirname(__file__),
        '..', '..', 'util',
        'config_files')
    click.echo('\t'.join(sorted([x[:-5] + (' ' * (20 - len(x[:-5])))
                                 for x in os.listdir(path)])))
    ctx.exit()
   

@click.command('config',
               help=HELP_TEXT,
               short_help='Setup directories and functions for QoL.')
@click.option('-g', '--get',
              help='Get current config', is_flag=True,
              callback=get_config, is_eager=True)
@click.option('-c', '--clear',
              help='Clear current config', is_flag=True,
              callback=clear_config, is_eager=True)
@click.option('-S', '--see',
              help='List saved configs.', is_flag=True,
              callback=get_saved_configs, is_eager=True)
@click.option('-t', '--tf-file',
              help='TF file, defaults to main.tf', default=None)
@click.option('-s3', '--s3-bucket',
              help='Set s3 bucket', default=None)
@click.option('-k', '--s3-key',
              help='Set s3 key', default=None)
@click.option('-n', '--name',
              help='Set lambda function name', default=None)
@click.option('-r', '--requirements',
              help='Requirements for your package', default=None)
@click.option('-s', '--script',
              help='Script file location', default=None)
@click.option('-pkg', '--package',
              help='Zipped package to deploy. Defaults to your lambda name.',
              default=None)
@click.option('-rep', '--replace',
              help='Replace all instances of a string', nargs=2,
              required=False, default=None)
@click.option('-save',
              help='Save config file.', nargs=1, type=str, default=None)
@click.option('-open', 'open_',
              help='Open config file.', nargs=1, type=str, default=None)
@click.option('-load',
              help='Loads the config from the current directory.',
              is_flag=True, default=False)
def cli(tf_file, s3_bucket, s3_key, name, get, clear, requirements,
        script, package, replace, save, open_, see, load):
   
    config = ConfigLoader.load_config()

    # Clears config if name is changed to avoid user error
    if name is not None:
        for key, value in config.items():
            if key == 'tf_file':
                config[key] = 'main.tf'
            else:
                config[key] = None

    ConfigLoader.save_config(config)
    run_file_options(
        tf_file       = tf_file, 
        s3_bucket     = s3_bucket,
        s3_key        = s3_key, 
        name          = name,
        requirements  = requirements,
        script        = script,
        package       = package
    )
    
    run_general_options(get, clear, replace, save, open_, load) 

    sys.exit(0)


def run_file_options(**kwargs):
    """
    Sets various config parameters.
    """
    config = ConfigLoader.load_config()
    for option, filepath in kwargs.items():
        if option in ['s3_bucket', 's3_key', 'name'] and filepath is not None:
            if option == 'name':
                _package_dir = Path(os.path.join(os.path.dirname(__file__),
                                                 '..', '..',
                                                 'deployment_packages',
                                                 filepath))
                if _package_dir.exists() is False:
                    os.makedirs(_package_dir)
                config['package'] = _package_dir.resolve().__str__()
                config['name'] = filepath
            else:
                config[option] = filepath
            continue

        if filepath is not None and filepath != 'main.tf':
            _filepath = Path(filepath)
            if _filepath.is_file() or _filepath.is_dir():
                config[option] = _filepath.resolve().__str__()
            else:
                click.secho('Improper file name or file doesn\'t exist.', fg='red')  
                sys.exit(1)

    ConfigLoader.save_config(config)


def run_general_options(get, clear, replace, save, open_, load):
    """
    Runs config options not related to setting config options
    """
    config = ConfigLoader.load_config()

    if replace != ():
        for key, value in config.items():
            if value is not None:
                config[key] = value.replace(replace[0], replace[1])
        ConfigLoader.save_config(config)

    if open_ is not None:
        try:
            _path = Path(os.path.join(os.path.dirname(__file__),
                                      '..', '..', 'util',
                                      'config_files', open_ + '.json'))
            with open(_path, 'r') as f:
                config = json.load(f)
            ConfigLoader.save_config(config)
        except IOError as e:
            click.secho(e, fg='red')
            sys.exit(1)

    if save is not None:
        with open(os.path.join(os.path.dirname(__file__),
                               '..', '..', 'util',
                               'config_files', save + '.json'), 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)

    if load:
        config = ConfigLoader.add_defaults(config)

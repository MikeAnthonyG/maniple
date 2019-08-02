import click
import hcl
import json
import os
import typing
import sys
import re

from pathlib import Path
from typing import Dict


class ConfigLoader():

    @staticmethod
    def load_config():
        with open('config.json', 'r') as f:
            return json.load(f)
       
    @staticmethod
    def save_config(config):
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)


    @staticmethod
    def add_defaults(config=None):
        if config is None:
            config = ConfigLoader.load_config()
            
        try:
            with open(config['tf_file'], 'r') as f:
                tf = hcl.load(f)
        except FileNotFoundError:
            click.secho('Main terraform file not found.', fg='red')
            sys.exit(1)
            
        if config['name'] is None:
            possible_names = ConfigLoader.get_possible_resources(tf)
            str_ = 'Select resource to deploy:\n'
            for resource in possible_names:
                if resource[2] == 'module':
                    str_ = str_ + '{}: {} (module)\n'.format(
                        resource[0],
                        resource[1]
                    )
                else:
                    str_ = str_ + '{}: {}\n'.format(
                        resource[0],
                        resource[1]
                    )
            user_input = 0
            user_input = click.prompt(str_, type=int)            
            while user_input < 1 and user_input > len(possible_names):
                try:
                    for resource in possible_names:
                        if user_input == resource[0]:
                            config['name'] = resource[1]
                except IndexError:
                    click.echo('Input integer of the resource (1-{})'.format(
                        len(possible_names)
                    ))
                    pass

        tf_vars = ConfigLoader.load_lambda_resource(config['name'], tf)
        try:
            runtime = tf_vars['resource']['aws_lambda_function'][config['name']]['runtime']
            handler = tf_vars['resource']['aws_lambda_function'][config['name']]['handler'].split('.')[0]
        except KeyError:
            click.echo('Terraform file missing required fields:\nruntime\nhandler')
            sys.exit(1)

        # Load files and directories
        path = Path('.')
        for x in path.iterdir():
            if x.is_dir():
                config = ConfigLoader.handle_load_dirs(config, runtime, handler, tf_vars, x)
            else:
                config = ConfigLoader.handle_load_files(config, handler, x)
                   
        for key, value in config.items():
            if value is None:
                click.secho('Warning: config variable {} not set!'.format(key))
        ConfigLoader.save_config(config)
        return


    @staticmethod
    def get_possible_resources(tf: Dict) -> Dict[str, str]:
        fns = []
        count = 1
        try:
            modules = tf['module']
            for module_name, values in modules.items():
                source = values['source']
                if source[0] == '/':
                    del source[0]
                try:
                    with open(os.path.join(os.getcwd(), source)) as f:
                        tf_module = hcl.load(f)
                    try:
                        if tf_module['resource']['aws_lambda_function'] is not None:
                            fns.append((count, module_name, 'module'))
                            count += 1 
                    except KeyError:
                        continue  # No lambda resource
                except FileNotFoundError:
                    click.secho('Module {} source doesn\'t exist'.format(
                        module_name), fg='red')
                    sys.exit(1)
        except KeyError:
            pass
        try:
            for name, values in tf['aws_lambda_function'].items():
                fns.append((count, name, 'resource'))
                count += 1 
        except KeyError:
            click.secho('No lambda resources in terraform file.', fg='red')
        return fns

    @staticmethod
    def load_lambda_resource(name, tf):
        try:
            return tf['resource']['aws_lambda_function'][name]
        except KeyError:  # Module
            try:
                source = tf['module'][name]['source']
                return ConfigLoader._load_module_source(name, source)
            except KeyError:
                click.echo('Source variable in module.')

    @staticmethod
    def _load_module_source(name, source):
        try:
            with open(os.path.join(os.getcwd(), source)) as f:
                tf_module = hcl.load(f)
            try:
                return tf_module['resource']['aws_lambda_function'][name]
            except KeyError:
                click.secho('No lambda resource in module with {}'.format(name))
        except FileNotFoundError:
            click.secho('Module {} source doesn\'t exist'.format(
                name), fg='red')
            sys.exit(1)

    @staticmethod
    def handle_load_dirs(config, handler, dir_):
        # Check if handler script exists in directory
        for f in dir_.iterdir():
            if f.split('.')[0] == handler:
                config['script'] = dir_
        return config

    @staticmethod
    def handle_load_files(config, runtime, handler, tf, file_):
        filename = file_.split('.')
        if config['script'] is None:
            if filename[-1] == 'js' and 'nodejs' in runtime and handler == filename[0]:
                config['script'] = Path(file_).resolve().__str__()
            if filename[-1] == 'py' and 'python' in runtime and handler == filename[0]:
                config['script'] = Path(file_).resolve().__str__()
        elif filename[-1] == 'txt' or filename[-1] == 'json':
            if config['requirements'] is None:
                if file_ == 'requirements.txt' or file_ == 'package.json':
                    config['requirements'] = Path(file_).resolve().__str__()
                if config['name'] == filename[0]:
                    config['requirements'] = Path(file_).resolve().__str__()
            if filename[0] == config['name']:
                # Override config if it is loaded with requirements.txt
                config['requirements'] = Path(file_).resolve().__str__()
        if file_ == config['tf_file']:
            try:
                if config['s3_bucket'] is None:
                    config['s3_bucket'] = tf['resource']['aws_lambda_function'][config['name']]['s3_bucket']
                if config['s3_key'] is None:
                    config['s3_key'] = ConfigLoader._determine_version(
                        tf['resource']['aws_lambda_function'][config['name']]['s3_key'],
                        tf)
            except KeyError:
                click.echo('S3 Bucket or S3 Key aren\'t set in the terraform file.')
                sys.exit(1)
        return config

    @staticmethod
    def _determine_version(key, tf):
        parsed_key = []
        for x in key.strip('/').split('/'):
            try:
                match = re.match('\${var\.(.*)}', x)
                if match is not None:
                    parsed_key.append(x.replace(x, tf['variable'][match.group(1)]['default']))
                else:
                    parsed_key.append(x)
            except KeyError:
                click.secho('Failed to handle S3 Key terraform variables.', fg='red')
                sys.exit(1)
        return '/'.join(parsed_key)

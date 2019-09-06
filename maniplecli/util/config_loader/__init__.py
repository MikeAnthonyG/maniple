import click
import hcl
import json
import logging
import os
import sys
import re

from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ConfigLoader():

    @staticmethod
    def load_config():
        try:
            with open(os.path.join(Path(__file__).parent, 'config.json'), 'r') as f:
                return json.load(f)
        except json.decoder.JSONDecodeError:
            click.echo('Config may be corrupted. Resetting...')
            config = ConfigLoader.reset_config()
            with open(os.path.join(Path(__file__).parent, 'config.json'), 'w') as f:
                json.dump(config, f, indent=2, sort_keys=True)
            logger.debug('Reset config file to default.')
            sys.exit(0)
       
    @staticmethod
    def save_config(config):
        with open(os.path.join(Path(__file__).parent, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)

    @staticmethod
    def load_terraform(tf_file):
        try:
            with open(tf_file, 'r') as f:
                return hcl.load(f)
        except FileNotFoundError:
            click.secho('Main terraform file not found.', fg='red')
            sys.exit(1)

    @staticmethod
    def reset_config():
        return {
            'name': None,
            'package': None,
            'requirements': None,
            's3_bucket': None,
            's3_key': None,
            'script': None,
            'tf_file': 'main.tf'
        }  

    @staticmethod
    def add_defaults(config=None):
        if config is None:
            config = ConfigLoader.load_config()
            
        tf = ConfigLoader.load_terraform(config['tf_file'])
            
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
            # Exit if there is only one resource
            if len(possible_names) == 1:
                config['name'] = possible_names[0][1]
            else:
                user_input = 0
                while user_input < 1 or user_input > len(possible_names):
                    user_input = click.prompt(str_, type=int)
                    try:
                        for resource in possible_names:
                            if user_input == resource[0]:
                                config['name'] = resource[1]
                    except IndexError:
                        click.echo('Input integer of the resource (1-{})'.format(
                            len(possible_names)
                        ))
            
        tf_vars = ConfigLoader.load_lambda_resource(config['name'], tf)
        logger.debug('Variables to load to config: {}'.format(tf_vars))
        try:
            runtime = tf_vars['runtime']
            handler = tf_vars['handler'].split('.')[0]
        except KeyError as e:
            click.echo('Terraform file missing required fields:\nruntime\nhandler')
            logger.error('{}: Terraform file missing either runtime or handler'.format(e))
            sys.exit(1)
        except TypeError as e:
            logger.error('User tried to -load from different config. \n{}'.format(e))
            click.echo('Config file doesn\'t match directory.')
            user_input = click.confirm('Reset config and load?', abort=True)
            return ConfigLoader.add_defaults(ConfigLoader.reset_config())

        # Have to find the package if it doesn't exist
        package_dir = Path(os.path.join(
            Path(__file__).parent,
            '..', '..', 'deployment_packages', config['name']))
        if package_dir.exists() is False:
            os.makedirs(package_dir)
        config['package'] = package_dir.resolve().__str__()
        # Load files and directories
        path = Path('.')
        for x in path.iterdir():
            if x.is_dir():
                config = ConfigLoader.handle_load_dirs(config, handler, x)
            else:
                config = ConfigLoader.handle_load_files(config, runtime, handler, tf_vars, tf, x)
                   
        for key, value in config.items():
            if value is None:
                click.secho('Warning: config variable {} not set!'.format(key))
                logger.debug('add_defaults failed to add {}: {}'.format(key, value))
                sys.exit(1)
        ConfigLoader.save_config(config)
        logger.debug('Default config loaded as:\n{}'.format(config))
        return config


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
                    with open(os.path.join(os.getcwd(), source, 'main.tf'), 'r') as f:
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
            for name, values in tf['resource']['aws_lambda_function'].items():
                fns.append((count, name, 'resource'))
                count += 1 
        except KeyError:
            pass
        return fns

    @staticmethod
    def load_lambda_resource(name, tf):
        try:
            lambda_resource = tf['resource']['aws_lambda_function'][name]
            return lambda_resource
        except KeyError:  # Module
            try:
                source_vars = tf['module'][name]
                resource_vars = ConfigLoader._load_module_source(
                    name,
                    tf['module'][name]['source'])
                module_resource = None
                tf_vars = {}
                for lambda_key in resource_vars.keys():
                    for key in source_vars.keys():
                        if key in resource_vars[lambda_key]['function_name']:
                            module_resource = resource_vars[lambda_key]
                            break

                if module_resource is None:
                    click.secho('Unable to determine lambda resource in module',
                                fg='red')
                    sys.exit(1)

                for tf_var_key in module_resource.keys():
                    for source_key, source_value in source_vars.items():
                        if source_key in module_resource[tf_var_key]:
                            tf_vars[tf_var_key] = source_value

                # Return dictionary with the keys updated from tf_vars
                return dict(module_resource, **tf_vars)
            except KeyError:
                logger.debug('Can\'t find module source')
                click.echo('Can\'t find module source.')

    @staticmethod
    def _load_module_source(name, source):
        try:
            with open(os.path.join(os.getcwd(), source, 'main.tf')) as f:
                tf_module = hcl.load(f)
            try:
                # Each variable needs to fit the lambda module
                return tf_module['resource']['aws_lambda_function']
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
            if f.is_file():
                possible_script = f.name
                if possible_script.split('.')[0] == handler:
                    config['script'] = dir_.resolve().__str__()
        return config

    @staticmethod
    def handle_load_files(config, runtime, handler, tf_vars, tf, file_):
        filename = file_.name.split('.')
        if config['script'] is None:
            if filename[-1] == 'js' and 'nodejs' in runtime and handler == filename[0]:
                config['script'] = file_.resolve().__str__()
            if filename[-1] == 'py' and 'python' in runtime and handler == filename[0]:
                config['script'] = file_.resolve().__str__()
        if filename[-1] == 'txt' or filename[-1] == 'json':
            if config['name'] == filename[0]:
                config['requirements'] = file_.resolve().__str__()
            if file_.name == 'requirements.txt' and 'python' in runtime:
                config['requirements'] = file_.resolve().__str__()
            if file_.name == 'package.json' and 'nodejs' in runtime:
                config['requirements'] = file_.resolve().__str__()
        if file_.name == config['tf_file']:
            try:
                if config['s3_bucket'] is None:
                    config['s3_bucket'] = tf_vars['s3_bucket']
                if config['s3_key'] is None:
                    config['s3_key'] = ConfigLoader.determine_version(
                        tf_vars['s3_key'],
                        tf)
            except KeyError:
                logger.debug('Missing S3 bucket or key.')
                click.echo('S3 Bucket or S3 Key aren\'t set in the terraform file.')
                sys.exit(1)
        return config

    @staticmethod
    def determine_version(key, tf):
        parsed_key = []
        for x in key.strip('/').split('/'):
            try:
                match = re.match('\${var\.(.*)}', x)
                if match is not None:
                    parsed_key.append(x.replace(x, tf['variable'][match.group(1)]['default']))
                else:
                    parsed_key.append(x)
            except KeyError:
                logger.debug('Unable to set proper version to files.')
                click.secho('Failed to handle S3 Key terraform variables.', fg='red')
                sys.exit(1)
        return '/'.join(parsed_key)

    @staticmethod
    def get_runtime(config=None):
        if config is None:
            config = ConfigLoader.load_config()
            
        tf = ConfigLoader.load_terraform(config['tf_file'])
            
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
            # Exit if there is only one resource
            if len(possible_names) == 1:
                config['name'] = possible_names[0][1]
            else:
                user_input = 0
                while user_input < 1 or user_input > len(possible_names):
                    user_input = click.prompt(str_, type=int)
                    try:
                        for resource in possible_names:
                            if user_input == resource[0]:
                                config['name'] = resource[1]
                    except IndexError:
                        click.echo('Input integer of the resource (1-{})'.format(
                            len(possible_names)
                        ))
            # Have to find the package if it doesn't exist
            package_dir = Path(os.path.join(
                Path(__file__).parent,
                '..', '..', 'deployment_packages', config['name']))
            if package_dir.exists() is False:
                os.makedirs(package_dir)
            config['package'] = package_dir.resolve().__str__()
            
        tf_vars = ConfigLoader.load_lambda_resource(config['name'], tf)
        logger.debug('Variables to load to config: {}'.format(tf_vars))

        try:
            return tf_vars['runtime']
        except KeyError:
            click.echo('Terraform file missing required fields:\nruntime\nhandler')
            sys.exit(1)
        except TypeError:
            logger.error("User tried to load config from another working directory")
            click.echo('Load correct resource/module with \'maniple config -n resource_name\' or \'maniple config -c\'')
            sys.exit(1)
        return None

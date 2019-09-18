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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger.setLevel(logging.INFO)

# TODO: complete refactor


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
        """
        Loads config file with data from the main.tf file.
        Default config param so won't overwrite user supplied config values.

        Args:
            config: config dictionary with values
        """
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
        logger.debug('add_defaults: Variables to load to config: {}'.format(tf_vars))
        try:
            runtime = tf_vars['runtime']
            handler = tf_vars['handler'].split('.')[0]
        except KeyError as e:
            click.echo('Terraform file missing required fields:\nruntime\nhandler')
            logger.error('{}: Terraform file missing either runtime or handler'.format(e))
            sys.exit(1)
        except TypeError as e:
            logger.error('add_defaults: User tried to -load from different config. \n{}'.format(e))
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
        logger.debug('add_defaults: Default config loaded as:\n{}'.format(config))
        return config

    @staticmethod
    def get_possible_resources(tf: Dict) -> Dict[str, str]:
        """
        Gets all possible lambda resources from a main.tf file.
        These could be resources or modules.

        Args:
            tf: main.tf file loaded as a dictionary

        Returns:
            A dictionary with all lambda resources/modules
        """
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
        """
        Loads a specific TF aws_lambda_function

        TODO: remove in and add regex
        Handle TF vars

        Args:
            name: name of lambda function
            tf: main.tf values as a dictionary

        Returns:
            A dictionary of all values related to the specific function.
        """
        try:
            lambda_resource = tf['resource']['aws_lambda_function'][name]
            return lambda_resource
        except KeyError:  # Module
            module_resource = None
            found_source = False
            module_key = ''
            tf_vars = {}
            try:
                for mod in tf['module']:
                    for key, val in tf['module'][mod].items():
                        if name == val:
                            found_source = True
                            module_key = key
                    if found_source:
                        module_resource = ConfigLoader._find_resource_from_var(
                            name,
                            tf['module'][mod]['source'],
                            module_key
                        )
                        source_vars = tf['module'][mod]
                        break
            except KeyError:
                logger.debug('load_lambda_resource: no module in main')                   

            if module_resource is None:
                click.secho('Unable to determine lambda resource in module',
                            fg='red')
                sys.exit(1)

            ConfigLoader.replace_module_vars(
                source_vars,
                module_resource
            )

            return module_resource

    @staticmethod
    def _load_module_source(name, source):
        """
        Loads a specific TF module from the source aws_lambda_function

        Args:
            name: name of lambda function
            source: source main.tf values as a dictionary

        Returns:
            A dictionary of all values related to the specific module.
        """
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
    def _find_resource_from_var(name, source, module_key):
        """
        Finds a resource from a modules value.
        e.g. function_name = ${var.lambda_name}
        in the module.
        """
        module_lambda_resources = ConfigLoader._load_module_source(name, source)
        for lambda_resource in module_lambda_resources:
            if module_key in module_lambda_resources[lambda_resource]['function_name']:
                return module_lambda_resources[lambda_resource]
        return None
        
    @staticmethod
    def handle_load_dirs(config, handler, dir_):
        """
        Searches directories for the script with the handler specified.

        Args:
            config: config dict
            handler: the handler value from the TF file
            dir_: directory to search

        Returns:
            An updated config dict
        """
        for f in dir_.iterdir():
            if f.is_file():
                possible_script = f.name
                if possible_script.split('.')[0] == handler:
                    config['script'] = dir_.resolve().__str__()
        return config

    @staticmethod
    def handle_load_files(config, runtime, handler, tf_vars, tf, file_):
        """
        Finds files not in a directory. TODO: update

        Args:
            config: config dict
            runtime: runtime value from TF file
            handler: the handler value from the TF file
            tf_vars: variables from the TF file
            tf: loaded TF file
            file__: file to handle

        Returns:
            An updated config dict
        """
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
        """
        Determines version in the terraform main file.
        """
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
    def replace_module_vars(source_vars, module_vars):
        """
        Replaces terraform variables in a module's source with the TF vars
        from main.tf
        """
        module_no_tf_vars = {}
        for key, value in source_vars.items():
            key_hcl_format = '${var.' + key + '}'
            for mod_key, mod_value in module_vars.items():
                try:
                    if key_hcl_format in mod_value:
                        modified_value = mod_value.replace(
                            key_hcl_format,
                            value
                        )
                        module_no_tf_vars[mod_key] = modified_value
                except TypeError:
                    continue
        module_vars.update(module_no_tf_vars)
        return module_vars

    @staticmethod
    def get_runtime(config=None):
        """
        Returns the runtime specified in the TF file.
        """
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

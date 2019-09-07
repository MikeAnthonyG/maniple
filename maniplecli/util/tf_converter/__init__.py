import click
import hcl
import logging
import os
import re
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TerraformConverter():
    @staticmethod
    def load_terraform(tf_file):
        try:
            with open(tf_file, 'r') as f:
                return hcl.load(f)
        except FileNotFoundError:
            click.secho('Main terraform file not found.', fg='red')
            sys.exit(1)

    @staticmethod
    def cloud_formation_bare_template():
        return {
            'Type': 'AWS::Lambda::Function',
            'Properties': {
                'Code': {},
                'Environment': {},
                'FunctionName': '',
                'Handler': '',
                'MemorySize': 128,
                'Role': '',
                'Runtime': '',
                'Timeout': 1
            }
        }

    def to_cloudformation(self, config):
        """
        Converts terraform to a basic cloudformation file.

        Args:
            config: config dictionary
        
        Returns:
            cf_template: dictionary with cloudformation style
        """
        cf_template = TerraformConverter.cloud_formation_bare_template()
        tf_resource = self.get_resource_attrs(
            TerraformConverter.load_terraform(config['tf_file']),
            config['name'])
        if tf_resource is None:
            logger.debug('Failed to find resource. Check terraform files.')
            sys.exit(1)
        for key, value in cf_template['Properties'].items():
            camel_case_key = self.to_camel_case(key)
            if camel_case_key in tf_resource.keys():
                cf_template['Properties'][key] = tf_resource[camel_case_key]
        # Add package zip file location as the code to invoke locally
        cf_template['Properties']['Code'] = config['package'] + '.zip'
        return cf_template

    def get_resource_attrs(self, tf, name):
        """
        Gets all values necesary to create the cloudformation dict.

        Args:
            tf: dictionary loaded from the main terraform file
            name: name of Lambda fn

        Returns:
            cf_template: dictionary with the cloudformation style
        """

        # Find if resource
        try:
            resources = tf['resource']['aws_lambda_function']
            for lambda_name, values in resources.items():
                if lambda_name == name:
                    return values
        except KeyError as e:
            logger.debug(e)
            pass
        except TypeError as e:
            logger.debug(e)
            pass

        # Find if module
        try:
            modules = tf['module']
        except KeyError as e:
            logger.debug(e)
            return None

        for module_name, values in modules.items():
            print(module_name)
            print(values)
            if module_name == name:
                source = values['source']
                with open(os.path.join(os.getcwd(), source, 'main.tf'), 'r') as f:
                    tf_module = hcl.load(f)
                lambda_resource = tf_module['resource']['aws_lambda_function']
                lambda_vars = lambda_resource[list(lambda_resource.keys())[0]]
                # Zip module into a basic resource format
                cf_template = {}
                for key, val in lambda_vars.items():
                    if '${var.' in val:
                        # Updates resource value from the module
                        match = re.match('\${var\.(.*)}', val)
                        cf_template[key] = values[match.group(1)]
                    else:
                        cf_template[key] = val
                print(cf_template)
                return cf_template

        logger.debug('Unable to get resource attrs')
        return None

    def to_camel_case(self, str_):
        """Converts snake case to camel case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str_)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

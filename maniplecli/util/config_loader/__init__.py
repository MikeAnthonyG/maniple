import click
import hcl
import os
import sys
import re

from pathlib import Path


class ConfigLoader():

    @staticmethod
    def add_defaults(config):
        try:
            with open(config['tf_file'], 'r') as f:
                tf = hcl.load(f)
            try:
                runtime = tf['resource']['aws_lambda_function'][config['lambda_name']]['runtime']
                handler = tf['resource']['aws_lambda_function'][config['lambda_name']]['handler'].split('.')[0]
            except KeyError as e:
                click.secho("Lambda resource with name {} not found in .tf file.\nSkipping auto-load...".format(config['lambda_name']), fg="red")
                return config
        except FileNotFoundError as e:
            click.secho("Main terraform file not found!", fg="red")
        path = Path(".")
        files = os.listdir(path) 
        for f in files:
            if config['script'] == None:
                if f[-2:] == 'js' and 'nodejs' in runtime and handler == f[:-3]:
                    config['script'] = Path(f).resolve().__str__()
                if f[-2:] == 'py' and 'python' in runtime and handler == f[:-3]:
                    config['script'] = Path(f).resolve().__str__()
            if f == 'requirements.txt' and config['requirements'] == None and 'python' in runtime:
                config['requirements'] = Path(f).resolve().__str__()
            if f == 'package.json' and config['requirements'] == None and 'nodejs' in runtime:
                config['requirements'] = Path(f).resolve().__str__()
            if f == config['tf_file']:
                try:
                    if config['s3_bucket'] == None:
                        config['s3_bucket'] = tf['resource']['aws_lambda_function'][config['lambda_name']]['s3_bucket']
                    if config['s3_key'] == None:
                        config['s3_key'] = ConfigLoader._determine_version(tf['resource']['aws_lambda_function'][config['lambda_name']]['s3_key'], tf)
                except KeyError as e:
                    click.echo("Lambda name is not set or doesn't match the terraform file.")
                    sys.exit(1)
        return config

    @staticmethod
    def _determine_version(key, tf):
        parsed_key = []
        for x in key.strip('/').split('/'):
            try:
                match = re.match("\${var\.(.*)}", x)
                if match is not None:
                    parsed_key.append(x.replace(x, tf['variable'][match.group(1)]['default']))
                else:
                    parsed_key.append(x)
            except KeyError as e:
                click.secho("Failed to handle S3 Key terraform variables.", fg="red")
                sys.exit(1)
        return '/'.join(parsed_key)

import click
import logging
import json
import shutil
import sys
import tarfile

from pathlib import Path
from zipfile import ZipFile
from maniplecli.util.config_loader import ConfigLoader
from maniplecli.util.shell import Shell
from maniplecli.util.lambda_packages import lambda_packages

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PackageDownloader():

    @staticmethod
    def download_packages(script, requirements, package):
        runtime = ConfigLoader.get_runtime()
        if requirements is not None:
            if 'python' in runtime:
                PackageDownloader._handle_python_packages(
                    script, requirements, package
                )
            elif 'nodejs' in runtime:
                PackageDownloader._handle_js_packages(
                    script, requirements, package
                )
            else:
                logger.debug('Unsupported runtime.')
                click.echo('Runtime not supported.')
                sys.exit(1)
        else:
            click.echo('No requirements specified. No packages will be downloaded.')    

    @staticmethod
    def _handle_python_packages(script, requirements, package):
        # Find packages that can be replaced for python
        requirements_to_replace = []
        package_path = None
        with open(requirements, 'r') as f:
            for py_package in f:
                try:
                    package_name = py_package[:py_package.index('=')]
                except ValueError as e:
                    logger.debug('Python requirements.txt misconfigured: {}'.format(e))
                    continue
                package_path = PackageDownloader._check_for_packages_to_replace(
                    package_name
                )
                if package_path is not None:
                    package_path = Path(package_path)
                    PackageDownloader._unzip_package(package_path, package)
                else:
                    requirements_to_replace.append(py_package)

        # Only install packages that haven't been replaced
        cmds = []
        if package_path is not None:
            for requirement in requirements_to_replace:
                cmds.append([
                    'pip',
                    'install',
                    '--target={}'.format(package),
                    requirement.strip()
                ])
        else:
            cmds.append([
                'pip',
                'install',
                '--target={}'.format(package),
                '-r',
                requirements
            ])
        for cmd in cmds:
            return_code, out, err = Shell.run(
                cmd,
                Path.cwd()
            )
            if return_code != 0:
                click.secho('{} failed.'.format(cmd), fg='red')
                logger.debug(err)
                sys.exit(1)        

    @staticmethod
    def _handle_js_packages(script, requirements, package):
        try:
            with open(requirements, 'r') as f:
                dependencies = json.load(f)
        except FileNotFoundError:
            click.echo('Can\'t find package.json - use \'maniple config -r\' to set value')
            sys.exit(1)
        for key, value in dependencies['dependencies'].items():                
            return_code, out, err = Shell.run(
                ['npm', '--prefix', package, 'install', 'key'],
                Path.getcwd()
            )
            if return_code != 0:
                click.secho('{} failed.'.format('npm package install'), fg='red')
                logger.error(err)
                sys.exit(1)

    @staticmethod
    def _check_for_packages_to_replace(package_name):

        user_input_str = ['{} can be replaced.'.format(package_name)]

        if package_name in lambda_packages.keys():
            logger.debug('Found replacable package: {}'.format(package_name))
            lambda_package = lambda_packages[package_name]

            package_to_replace = {}
            i = 1
            for versions in lambda_package.keys():
                user_input_str.append(
                    '{} ({}): {}=={}'.format(i, versions, package_name,
                                             lambda_package[versions]['version'])
                )
                package_to_replace[i] = lambda_package[versions]['path']
                i += 1
            user_input_str.append('{}: Install from pip\n'.format(i))
            user_input = click.prompt('\n'.join(user_input_str))
            try:
                user_input = int(user_input)
                if user_input in range(1, len(package_to_replace.keys()) + 1):
                    return package_to_replace[user_input]
                else:
                    return None
            except ValueError:
                logger.debug('User didn\'t replace package.')
                return None
        else:
            return None

    @staticmethod
    def _unzip_package(package_path, deployment_package):
        if package_path.suffix == '.tar':
            tar = tarfile.open(package_path, 'r:')
            tar.extractall(deployment_package)
            tar.close()
        elif package_path.suffix == '.gz':  # .tar.gz
            tar = tarfile.open(package_path, 'r:gz')
            tar.extractall(deployment_package)
            tar.close()
        elif package_path.suffix == '.zip':
            with ZipFile(package_path, 'r') as f:
                f.extractall(deployment_package)
        else:
            logger.debug('Can\'t unzip package {}'.format(package_path))
            click.secho('Unable to unzip package: {}'.format(
                package_path.name), fg='red')

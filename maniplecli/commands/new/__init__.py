import click
import importlib.util
import logging
import os
import sys

from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HELP_TEXT = '''
Creates a template with the main file components to run Lambda functions

    maniple new [TEMPLATE] [NAME]

Create new python function: 
$ maniple new pyapp my_python_fn \n
\b
Create new javascript function:
$ maniple new jsapp my_js_fn 
'''

@click.command(
    'new',
    help=HELP_TEXT,
    short_help='Create new function directory structure')
@click.argument('template')
@click.argument('name')
def cli(template, name):
    logger.debug('template: {}'.format(template))
    logger.debug('name: {}'.format(name))
    parent_dir = Path(__file__).parent
    if not Path(parent_dir, template).exists():
        click.echo('No template with name \'{}\' exists!'.format(template))
        sys.exit(1)

    # Import correct module based on template
    spec = importlib.util.spec_from_file_location(
        '{0}.{0}'.format(template),
        '{}/{}/__init__.py'.format(parent_dir, template)
    )
    spec_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spec_app)
    class_ = getattr(spec_app, template)
    app = class_(name)
    app.run()
    sys.exit(0)

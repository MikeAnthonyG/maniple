"""
Entry point for the CLI
"""

import click
import colorama
import json
import logging

from pyfiglet import Figlet
from clint.textui import puts, colored
from os.path import dirname

from .command import BaseCommand

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')



def common_options(f):
    return 

def print_info(ctx, param, value):
    if value is False:
        return

    fig = Figlet(font='lean')
    puts(colored.red(fig.renderText('maniple')))
    click.echo("Serverless framework for Terraform.")
    ctx.exit()

@click.command(cls=BaseCommand)
@click.option("--info", is_flag=True, is_eager=True, callback=print_info)
def cli(info):
    "Serverless framework for Terraform."
    pass


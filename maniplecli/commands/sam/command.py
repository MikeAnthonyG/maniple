import click
import logging
import json
import os
import platform
import subprocess

from subprocess import Popen, PIPE

HELP_TEXT = """
Invoke SAM patterns. 

\n
Watch the logs of a function.
$ maniple sam -w \n
\b
"""
with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json"), 'r') as f:
    CONFIG = json.load(f)

@click.command("sam",help=HELP_TEXT, short_help="Invoke user defined SAM patterns")
@click.option("-w", "--watch", help="Watch the logs of a function.", is_flag=True)
@click.option("-e", "--error-logs", help="Watch the error logs of a function.", is_flag=True)
@click.option("-n", "--new-terminal", help="Open in new terminal", is_flag=True, default=False)
@click.option("-l", "--lambda_name", help="Lambda name to view logs - defaults to config", default=CONFIG['lambda_name'])
def cli(watch, error_logs, new_terminal, lambda_name):
    run_cli(watch, error_logs, new_teriminal, lambda_name)

def run_cli(watch, error_logs, new_terminal, lambda_name):
    if watch:
        _watch(lambda_name, new_terminal)
    if error_logs:
        _error(lambda_name)
    sys.exit(0)

def _watch(lambda_name, new_terminal):
    all_logs_command = 'sam logs -n {} --tail'.format(lambda_name)
    if platform.system() == 'Windows':
        if new_terminal:
            subprocess.call('start ' + all_logs_command, shell=True)
        else:
            all_logs = Popen("cmd.exe", shell=True)
            all_logs.communicate(all_logs_command)
    else:
        click.secho("Not yet implemented.", fg="red")
 
def _error(lambda_name):
    error_logs_command = '''sam logs -n %s --tail --filter "error"''' % (lambda_name)
    if platform.system() == 'Windows':
        subprocess.call('start ' + error_logs_command, shell=True)
    else:
        click.secho("Not yet implemented.", fg="red")
 
        


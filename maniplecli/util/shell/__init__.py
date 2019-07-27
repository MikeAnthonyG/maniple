import json
import logging
import typing
import subprocess
import sys

from subprocess import PIPE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Shell():

    @staticmethod
    def run(cmd, pwd):
        stderr = PIPE
        stdout = PIPE
        
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr,
                             cwd=pwd)

        out, err = p.communicate()
        return_code = p.returncode

        return return_code, out, err

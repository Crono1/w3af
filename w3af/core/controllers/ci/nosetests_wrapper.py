#!/usr/bin/env python

import sys
import shlex
import subprocess
import multiprocessing

from termcolor import colored
from concurrent import futures


MAX_WORKERS = multiprocessing.cpu_count()
NOSETESTS = 'nosetests'
NOSE_PARAMS = '--with-yanc --with-doctest --doctest-tests'
SELECTORS = ["smoke and not internet and not moth and not root",]
TEST_DIRECTORIES = [
    # The order in which these are run doesn't really matter, but I do need to
    # take care of "grouping" (which directory is run) because of an incompatibility
    # between "w3af/core/ui/gui/" and "w3af/core/ui/tests/" which comes from
    # Gtk2 vs. Gtk3.
    'w3af/core/controllers/',
    'w3af/core/data/',
    'w3af/core/ui/tests/',
    'w3af/core/ui/console/',
    'w3af/core/ui/gui/',
    'w3af/plugins/',
]

NOISE = ['Xlib:  extension "RANDR" missing on display ":99".',
         'WARNING: Failed to execute tcpdump. Check it is installed and in the PATH',
         'Generating LALR tables',
         'WARNING: 2 shift/reduce conflicts']

def run_nosetests(selector, directory, params=NOSE_PARAMS):
    '''
    Run nosetests like this:
        nosetests $params -A $selector $directory
    
    :param selector: A string with the names of the unittest tags we want to run
    :param directory: Which directory do we want nosetests to find tests in
    :param params: The parameters to pass to nosetests
    :return: (stdout, stderr, exit code) 
    '''
    cmd = '%s %s -A "%s" %s' % (NOSETESTS, params, selector, directory)
    cmd_args = shlex.split(cmd)

    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
    )
    stdout, stderr = p.communicate()
    
    return cmd, stdout, stderr, p.returncode

def clean_noise(output_string):
    '''
    Removes useless noise from the output
    
    :param output_string: The output string, stdout.
    :return: A sanitized output string
    '''
    for noise in NOISE:
        output_string = output_string.replace(noise + '\n', '')
        output_string = output_string.replace(noise, '')
    
    return output_string

def summarize_exit_codes(exit_codes):
    '''
    Take a list of exit codes, if at least one of them is not 0, then return
    that number.
    '''
    for ec in exit_codes:
        if ec != 0: return ec
    
    return 0

def print_info_console(cmd, stdout, stderr, exit_code):
    print colored(cmd, 'green')
    print '=' * len(cmd)

    print clean_noise(stdout)
    print clean_noise(stderr)

if __name__ == '__main__':
    exit_codes = []
    future_list = []
    
    # TODO: Run the tests which require moth
    
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for selector in SELECTORS:
            for directory in TEST_DIRECTORIES:
                args = run_nosetests, selector, directory, NOSE_PARAMS
                future_list.append(executor.submit(*args))
                
        for future in futures.as_completed(future_list):
            cmd, stdout, stderr, exit_code = future.result()
            exit_codes.append(exit_code)

            print_info_console(cmd, stdout, stderr, exit_code)
            
    # We need to set the exit code.
    sys.exit(summarize_exit_codes(exit_codes))

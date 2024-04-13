'''Utility functions'''

import logging
import os
import subprocess
import sys


def get_abs_path(caller: str, filename: str) -> str:
    '''Concatenate the filename to the absolute location of the caller script

    Args:
        caller (str): the caller script

        filename (str): input filename

    Returns:
        str: the absolute path of the input filename
    '''
    script_path = os.path.realpath(os.path.dirname(caller))
    return os.path.join(script_path, filename)


def setup_logging(filename: str = None, verbose: bool = False) -> None:
    '''Set up logging facility

    Args:
        filename (str): the name of the log file

        verbose (bool): print debug information, as well.

    Returns:
        None
    '''
    file_params = {
        'filename': filename,
        'filemode': 'a',
    }
    stream_params = {
        'stream': sys.stdout
    }
    format_params = {
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'level': logging.DEBUG if verbose else logging.INFO,
    }
    if filename is not None:
        log_params = {**file_params, **format_params}
    else:
        log_params = {**stream_params, **format_params}
    logging.basicConfig(**log_params)


def execute(cmd: str) -> bool:
    '''Call an external command

    Args:
        cmd (str): the external command to execute

    Returns:
        bool: True if the execution succeed
    '''
    try:
        # Because of the flag check=True, subprocess will raise an
        # exception on the face of errors because we don't want to
        # check the result manually.
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        logging.error('Error occur when executing: %s', cmd)
        return False
    return True


def check_exists(name: str, is_file: bool) -> bool:
    '''Check if a file or a folder exists

    Args:
        name (str): the name of the file or folder

        is_file (bool) : a flag to indicate if we want to check
                         for a file or a folder

    Returns:
        True if the entity exists and the type matches
    '''
    if not os.path.exists(name):
        raise FileNotFoundError(name)
    if is_file:
        if not os.path.isfile(name):
            raise IsADirectoryError(name)
    else:
        if not os.path.isdir(name):
            raise NotADirectoryError(name)

'''Utility functions'''

import json
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


def execute(cmd: str, discard_error: bool = False) -> bool:
    '''Call an external command

    Args:
        cmd (str): the external command to execute

        discard_error (bool): skip logging error

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
        if not discard_error:
            logging.error('Error occur when executing: %s', cmd)
        return False
    return True


def check_exists(name: str, is_file: bool):
    '''Check if a file or a folder exists

    Args:
        name (str): the name of the file or folder

        is_file (bool): a flag to indicate if we want to check
                         for a file or a folder
    '''
    if not os.path.exists(name):
        raise FileNotFoundError(name)
    if is_file:
        if not os.path.isfile(name):
            raise IsADirectoryError(name)
    else:
        if not os.path.isdir(name):
            raise NotADirectoryError(name)


def load_config(config_filename: str, verbose: bool = False) -> dict:
    '''Load the configuration stored in a JSON file. The configuration must
    be stored with the key 'config'.

    args:
        config_filename (str): the JSON file storing the configuration
        verbose (bool): print the debug information or not

    returns:
        a dictionary containing the configuration
    '''
    # __file__ stores the absolute path of the python script
    # realpath() return the canonical path of the specified
    # filename by eliminating any symbolic links encountered
    # in the path
    script_path = os.path.realpath(os.path.dirname(__file__))
    config_abs_filename = os.path.join(script_path, config_filename)
    check_exists(config_abs_filename, is_file=True)

    config = None
    with open(config_abs_filename, encoding="utf-8") as config_file:
        if verbose:
            print(f'Loading config file: {config_abs_filename}')
        config_data = json.load(config_file)
        config = config_data.get('config', None)

    if config and "Destinations" in config:
        destinations = config["Destinations"]
        for _, folder in destinations.items():
            check_exists(folder, is_file=False)
    return config


class ConfigFileBase:
    '''The parent class for managing JSON config file'''
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.config = self.load_config()

    def load_config(self) -> dict:
        '''Load the configuration stored in a JSON file. The configuration must
        be stored with the key 'config'.

        Args:
            config_filename (str): the JSON file storing the configuration

        Returns:
            a dictionary containing the configuration
        '''
        check_exists(self.filename, is_file=True)

        with open(self.filename, encoding="utf-8") as config_file:
            logging.debug('Loading %s', self.filename)
            config_data = json.load(config_file)
            return config_data.get('config', None)

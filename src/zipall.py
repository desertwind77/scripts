#!/usr/bin/env python3
'''zip or unzip every file in the folder'''

from pathlib import Path
import argparse
import logging
import os
from utils import execute, setup_logging


def is_command_available(cmds: list[str]) -> bool:
    '''Check if the required commands are available or not

    Args:
        cmds (list[str]) : the list of commands to check

    Returns:
        bool: True if all commands are available
    '''

    for cmd in cmds:
        cur_cmd = [cmd, '-h']
        try:
            execute(cur_cmd)
        except FileNotFoundError:
            logging.error('Command %s not found', cmd)
            return False
    return True


def parse_arguments() -> argparse.Namespace:
    '''Parse the command line arguments

    Args:
        None

    Return:
        argparse.Namespace: parsed command line arguments
    '''
    parser = argparse.ArgumentParser(
            description='zip or unzip every file in a folder')
    parser.add_argument('-d', '--dryRun', action='store_true',
                        dest='dry_run', help='dry run')
    # Intentionally require --delete to avoid deleting the original files by
    # mistake.
    parser.add_argument('--delete', action='store_true',
                        help='delete the original files')
    parser.add_argument('-l', '--logfile', action='store',
                        dest='logfile',
                        help='log the message to the file instead of console')
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', help='print more detais')
    parser.add_argument('-u', '--unzip', action='store_true',
                        dest='unzip',
                        help='running unzip instead of zip')
    parser.add_argument('folder', action='store',
                        help='the folder containing files to zip or unzip')
    return parser.parse_args()


def zip_folder(folder: str,
               unzip: bool = False,
               ignored_list: list[str] = None,
               delete: bool = False,
               dry_run: bool = False) -> None:
    '''zip or unzip all files in the specific folder

    Args:
        folder (str): the folder to zip or unzip

        unzip (bool): unzip all the files instead of zip

        delete (bool): delete the original files

        dry_run (bool): dry run

    Returns:
        None
    '''
    # Make sure that the required commands are available.
    if not is_command_available(['zip', 'unzip']):
        return

    # Save the current directory and go to the target directory
    # so that we can look at all the files in that directory.
    current_dir = os.getcwd()
    os.chdir(folder)

    # Determine what to do with each file in the folder and
    # add the command to act on the file to a dictionary.
    # Later we can process this dictionary in parallel using
    # multiprocessing which works very well with I/O intensive
    # tasks like zipping and unzipping files.
    cmd_list = {}
    for cur_file in sorted(os.listdir('.')):
        cmd = None
        if unzip:
            # Skip the irrelevant files
            if Path(cur_file).suffix.lower() != '.zip':
                continue
            cmd = ['unzip', cur_file]
        else:
            # TODO: add support for zipping directories. Maybe add an argument
            # for this behavior.
            # TODO: add support for matching filenames with regular expressions
            # instead of exact match
            #
            # Skip if one of the following conditions is true:
            # 1) The filename is in the ignored list
            # 2) The file is a hidden file of which the filename begins with
            #    '.'.
            # 3) It is not a file. It could be a directory.
            if ((ignored_list is not None) and (cur_file in ignored_list)) or\
                    cur_file.startswith('.') or \
                    not os.path.isfile(cur_file):
                continue

            # Determint the destination filename
            destination = Path(cur_file).stem + '.zip'
            cmd = ['zip', destination, cur_file]
        cmd_list[cur_file] = cmd

    # TODO: add multiprocessing support
    for cur_file, cmd in cmd_list.items():
        logging.debug(' '.join(cmd))
        if dry_run:
            continue
        if not execute(cmd):
            # If we fail to zip or unzip the file, we should not delete it.
            continue
        if delete:
            os.remove(cur_file)

    # Change the current directory to the original directory
    os.chdir(current_dir)


def main():
    '''The main function'''
    # TODO: add an argument to add filename to the ignore list
    ignored_list = ['.DS_Store']

    args = parse_arguments()
    setup_logging(args.logfile, verbose=args.verbose)
    zip_folder(args.folder, unzip=args.unzip, ignored_list=ignored_list,
               delete=args.delete, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

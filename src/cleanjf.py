#!/usr/bin/env python3
'''
Remove auto-created files.
These files may make sense on one platform but not the others

As of now, I don't see any need to have an option to support
a user-specified config file. So I don't add this feature.
If need be, we can add this in the future.
'''

import argparse
import os
import shutil
from utils import load_config

CONFIG_FILENAME = 'config/cleanjf.json'


def process_file(junk_file_list, filename, verbose=False):
    '''
    Delete junk files (mac os).
    Return True if deleted; otherwise, False
    '''

    # Extract only the filename or directory name from the absolute path
    basename = os.path.basename(filename)
    if basename in junk_file_list:
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)

        if verbose:
            print(f'Removed {basename}')

        return True

    return False


def main():
    '''The main function'''
    parser = argparse.ArgumentParser(description='Remove all junk files')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Print log messages')
    parser.add_argument('folder', action='store', help='Folder to be cleaned')

    args = parser.parse_args()
    config = load_config(__file__, CONFIG_FILENAME, args.verbose)
    junk_file_list = config["filelist"]

    # Walk the directory tree. It is actually a tuple of (root, dirs, files)
    # But we don't use dirs here.
    for root, _, files in os.walk(args.folder, topdown=False):
        for file in files:
            filename = os.path.join(root, file)
            process_file(junk_file_list, filename, verbose=args.verbose)


if __name__ == '__main__':
    main()

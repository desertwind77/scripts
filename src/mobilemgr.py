#!/usr/bin/env python3
'''
Organize backup photos and videos from iPhone

Assuming that the source folder is at /src, we will organize the files into
/src/year/month/<date> <3-digit sequence number>.extension. The time is based
on their modified date.

Note that we don't check for file duplication.
'''

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import datetime
import os
import re
import shutil

from utils import load_config

CONFIG_FILENAME="config/mobilemgr.json"

@dataclass
class RenameInfo:
    '''Information on a file to be renamed'''
    src: Path
    dst: Path

    def __lt__(self, other):
        return self.dst < other.dst

    def __str__(self):
        return f'{self.src.absolute()} -> {self.dst.absolute()}'

    def rename(self):
        '''Rename the file'''
        shutil.move(self.src.absolute(), self.dst.absolute())

def populate_counter(cur_path, files):
    '''Populate the dictionary mapping from date to file count per date'''
    counter = defaultdict( int )
    # Populate the counter from existing files
    for file in files:
        if cur_path != file.parent:
            continue
        filename = str(file.stem)
        if (obj := re.match(r'(?P<date>\d{4}-\d{2}-\d{2}) (?P<count>\d{3})',filename)):
            date = obj.group('date')
            count = int(obj.group('count'))
            counter[date] = max(count, counter[date])
    return counter

def get_rename_info_list(cur_path, files, counter):
    '''Get the list of files to be renamed'''
    rename_info = []

    for file in files:
        if not os.path.isfile(file):
            continue
        # Get the modified time
        mod_timestamp  = os.path.getmtime(file)
        # Convert the unix timestamp to a human readable format
        mod_date = datetime.datetime.fromtimestamp(mod_timestamp)

        # Determine the destination folder
        dst_folder = f'{mod_date.year}/{mod_date.month:02d}'
        # Determine the destination filename
        mod_date_str = str(mod_date.date())
        counter[mod_date_str] += 1
        date_counter = counter[mod_date_str]
        ext = file.suffix.lower()
        dst_file = f'{mod_date_str} {date_counter:03d}{ext}'
        # Determine the final destination
        dst = cur_path / f'{dst_folder}/{dst_file}'

        if cur_path == file.parent:
            # We assume that the backup files are dumped into cur_path. We want
            # to skip all the subfolder of cur_path.
            if not os.path.isdir( dst_folder ):
                os.makedirs( dst_folder )
            if os.path.exists(dst):
                print(f'{dst} already exists')
                continue
            rename_info.append(RenameInfo(file, dst))

    return rename_info

def organize(source, dry_run=False):
    '''Organize files in the source folder'''
    if not os.path.isdir(source):
        print(f'The folder {source} does not exist')
        return

    # Save the current working directory
    cur_dir = os.getcwd()
    # Change to the folder to process
    os.chdir(source)

    cur_path = Path('.')
    files = sorted(list(cur_path.glob('**/*.*')))

    counter = populate_counter(cur_path, files)
    rename_info = get_rename_info_list(cur_path, files, counter)

    for info in sorted(rename_info):
        print(info)
        if not dry_run:
            info.rename()

    # Restore the original working directory
    os.chdir(cur_dir)

def main():
    '''The main program'''
    config = load_config( __file__, CONFIG_FILENAME )
    backups = config.get( 'mobile_backup' )
    assert backups, f"mobile_backup is missing from {CONFIG_FILENAME}"
    assert isinstance(backups, list)

    # Parse the command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dry-run',action='store_true',
                        help='dry run')
    args = parser.parse_args()

    for backup in backups:
        organize(backup, dry_run=args.dry_run)

if __name__ == '__main__':
    main()

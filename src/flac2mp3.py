#!/usr/bin/env python3
'''Convert from flac to mp3'''

from concurrent.futures.process import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List
import argparse
import concurrent
import os
import re
import subprocess
import sys

# pylint: disable=import-error
from fastprogress import progress_bar
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import APIC
from pydub import AudioSegment
from pydub.utils import mediainfo


@dataclass(frozen=True)
class ConvertInfo:
    '''A class to store absolute path of the source FLAC file and the
    destination MP3'''
    src: str
    dst: str

    def __str__(self):
        return f'{self.src} ---> {self.dst}'


def parse_arguments() -> argparse.Namespace:
    '''Parse the command line argument

    Args:
        None

    Return:
        argparse.Namespace: parsed command line arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("dst", action="store",
                        help="Destination foler")
    parser.add_argument("folders", nargs="*",
                        help="Folders containing flac files")
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="Do not the conversion")
    parser.add_argument("-f", "--flatten", action="store_true",
                        help="Flattern the subfolder 'CD' and 'Disc'")
    parser.add_argument("-s", "--sequential", action="store_true",
                        help="Do not use parallel conversion")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print source and destination files")
    return parser.parse_args()


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
def process_all_folders(dst: str, folders: List[str],
                        flatten: bool = False) -> List[ConvertInfo]:
    '''
    Process all the folders in the arguments and return the list of (src,dst)

    Args:
        dst (str):

        folders (List[str]):

        flatten (bool):

    Return:
        l
    '''

    def sanity_check(folder: str) -> None:
        '''
        Check that
        1) If the folder contains FLAC files, it doens't have any CD
           or DISC folder
        2) The folder cannot contain subfolder CD and DISC at the same time

        Args:
            folder (str): the folder to check
        '''
        contents = os.listdir(folder)
        keyword_cd = any('cd' in c.lower() for c in contents)
        keyword_disc = any('disc' in c.lower() for c in contents)
        keyword_flac = any('.flac' in c.lower() for c in contents)
        assert not (keyword_cd and keyword_disc), \
            "CD and Disc are mutually exclusive"
        assert not ((keyword_cd or keyword_disc) and keyword_flac), \
            "CD/Disc and .flac are mutually exclusive"

    def get_copy_info(flac, dst_folder, mp3_folder=None, flatten=False):
        flac_str = str(flac)
        mp3 = os.path.splitext(flac.name)[0] + '.mp3'

        disc_no = None
        if flatten and 'CD' in flac_str:
            obj = re.search(r'CD (\d+)\/.*\.flac', flac_str)
            disc_no = int(obj.group(1)) if obj else None
        if flatten and 'Disc' in flac_str:
            obj = re.search(r'Disc (\d+).*\/.*\.flac', flac_str)
            disc_no = int(obj.group(1)) if obj else None

        if disc_no:
            mp3_folder = mp3_folder.split('/')[0]
            mp3 = f'{disc_no:02}_{mp3}'
            mp3 = os.path.join(dst_folder, mp3_folder, mp3)
        else:
            if mp3_folder:
                mp3 = os.path.join(dst_folder, mp3_folder, mp3)
            else:
                mp3 = os.path.join(dst_folder, mp3)
        return ConvertInfo(flac, mp3)

    for folder in folders:
        sanity_check(folder)

    copy_info = []
    current_dir = Path.cwd()
    for folder in folders:
        folder_path = Path(folder)
        flacs = sorted(list(folder_path.glob('**/*.flac')))
        if not flacs:
            continue

        for flac in flacs:
            parent = flac.parent.absolute()
            if current_dir == parent:
                # The flac files are in the current directory.
                copy_info.append(get_copy_info(flac, dst))
            else:
                parent_str = str(parent).split('/')
                if 'CD' in str(parent) or 'Disc' in str(parent):
                    mp3_folder = parent_str[-2:]
                else:
                    mp3_folder = parent_str[-1:]
                mp3_folder = os.path.join(*mp3_folder)
                copy_info.append(
                        get_copy_info(flac, dst, mp3_folder=mp3_folder, flatten=flatten))
    return copy_info


def convert(info: ConvertInfo) -> None:
    '''Convert a flac file to a mp3 file

    Args:
        info (ConvertInfo):
    '''
    path = os.path.split(info.dst)[0]
    if not os.path.exists(path):
        os.makedirs(path)

    # Copy tags from flac
    tags = mediainfo(str(info.src)).get('TAG', {})

    # Export from flac to mp3
    flac = AudioSegment.from_file(info.src, format="flac")
    flac.export(info.dst, format="mp3", tags=tags)

    # Copy the album arts from flac to mp3
    flac_tags = FLAC(info.src)
    mp3_tags = MP3(info.dst)
    for pic in flac_tags.pictures:
        if pic.type != 3:
            continue

        apic = APIC(
                encoding=3,           # 3 is for UTF-8
                mime=pic.mime,        # image/jpeg or image/png
                type=pic.type,        # 3 is for the cover image
                desc=pic.desc,
                data=pic.data)
        mp3_tags.tags.add(apic)
    mp3_tags.save()


def convert_all_files(dst, copy_info, dry_run=False, seq_exec=False, verbose=False):
    '''Convert all the files in copy_info'''
    if not dry_run:
        # Recursively make the directory where os.mkdir() is the
        # non-recersive counterpart
        os.makedirs(dst, exist_ok=True)

    size = len(copy_info)
    cpu_count = os.cpu_count()

    if verbose:
        digits = len(str(size))
        for count, info in enumerate(copy_info):
            count_str = str(count + 1).rjust(digits, '0')
            print(f'{count_str}/{size}', info)

    if dry_run:
        return

    if seq_exec or size < 2 or cpu_count < 2:
        for info in copy_info:
            convert(info)
    else:
        # From my experimental result, the parallel execution is 10 times faster
        # on Mac Studio Ultra M1 with 20 CPU cores.
        with ProcessPoolExecutor(max_workers=cpu_count) as executor:
            tasks = [executor.submit(convert, i) for i in copy_info]
            for _ in progress_bar(concurrent.futures.as_completed(tasks), total=size):
                pass


def check_ffmpeg_exists():
    '''Check if ffmpeg is available; otherwise, terminate the programm'''
    try:
        cmd_tokens = ['which', 'ffmpeg']
        subprocess.check_output(cmd_tokens)
    except subprocess.CalledProcessError:
        print('Command not found: ffmpeg.')
        sys.exit(1)


def main() -> None:
    '''The main program'''
    check_ffmpeg_exists()

    args = parse_arguments()
    copy_info = process_all_folders(args.dst, args.folders, args.flatten)
    convert_all_files(args.dst, copy_info, dry_run=args.dry_run,
                      seq_exec=args.sequential, verbose=args.verbose)


if __name__ == '__main__':
    main()

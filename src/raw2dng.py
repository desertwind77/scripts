#!/usr/bin/env uv run --project /Users/athichart/Workspace/scripts
'''
Convert RAW files to .dng files

From the list of locatoins in a config file,
1) Convert all the RAW files to .dng files
2) Rename the .dng file to "<parent dir> <4-digit sequence number>.dng"

We need to install exiftool manually and also install freetype and ImageMagick
via brew.

brew install freetype imagemagick
'''
from dataclasses import dataclass
from pathlib import Path
import argparse
import asyncio
import os
import re
import shutil
# pylint: disable=import-error
from pydngconverter import DNGConverter, flags

from utils import load_config

CONFIG_FILENAME = "config/raw2dng.json"

IGNORED_FOLDERS = [ '.DS_Store' ]

@dataclass
class ConvertInfo:
    '''Conversion information'''
    src: Path
    dst: Path

async def convert_raw_to_dng(input_folder, output_folder):
    """
    Converts raw image files in input_folder to DNG format in output_folder.
    """
    pydng = DNGConverter(
        input_folder,
        dest=output_folder,
        jpeg_preview=flags.JPEGPreview.NONE,  # Embeds a JPEG preview
        fast_load=True,
    )
    await pydng.convert()

def is_eligible(file_path):
    '''Is a file eligible for conversion?'''
    if not os.path.isfile(file_path):
        return False
    if str(file_path.suffix).lower() not in [ '.arw', '.crw', '.nef', ]:
        return False
    dng = f'{str(file_path.stem)}.dng'
    return not os.path.exists(dng)

def find_convert_info(source, dry_run=False):
    '''Convert RAW files in the source folder'''
    # List of the temporary folders
    conversion_list = []

    src_path = Path(source)
    for folder in src_path.iterdir():
        if folder in IGNORED_FOLDERS:
            continue

        # Determine the RAW files
        files = list(folder.glob('**/*.*'))
        files = sorted([f for f in files if is_eligible(f)])

        if not files:
            print(f'Skip {folder}')
            continue
        print(f'Convert {folder}')

        # Create a temporary folder
        tmp_folder = folder / 'tmp'
        if not os.path.isdir(tmp_folder) and not dry_run:
            os.makedirs(tmp_folder)

        # Move the RAW files to the temporary folder
        if not dry_run:
            for file in files:
                shutil.move(file, tmp_folder)

        conversion_list.append(ConvertInfo(tmp_folder, folder))

    return conversion_list

def rename_file(source, dry_run=False):
    '''Rename files'''
    src_path = Path(source)
    for folder in src_path.iterdir():
        files = list(folder.glob('**/*.*'))
        files = [ f for f in files if str(f.suffix).lower() == '.dng' ]
        files = sorted(files)
        for seq, file in enumerate(files):
            if re.match(rf'{file.parent.stem} \d+', str(file.stem)):
                continue
            dst = f'{file.parent}/{file.parent.stem} {seq+1:04d}.dng'
            if os.path.exists(dst):
                continue
            print(f'Rename {file.absolute()} to {dst}')
            if not dry_run:
                shutil.move(file.absolute(), dst)

def main():
    '''The main program'''
    parser = argparse.ArgumentParser()
    parser.add_argument( '-d',  '--dry-run', action='store_true',)
    args = parser.parse_args()

    config = load_config( __file__, CONFIG_FILENAME )
    locations = config.get( 'locations' )
    assert locations, f"locations is missing from {CONFIG_FILENAME}"
    assert isinstance(locations, list)

    conversion_list = []
    for src in locations:
        conversion_list = find_convert_info(src, dry_run=args.dry_run)

    # Run the RAW converter
    loop = asyncio.get_event_loop()
    for c in conversion_list:
        if not args.dry_run:
            loop.run_until_complete(convert_raw_to_dng(c.src, c.dst))
    loop.close()

    # Delete all temporary folders
    if not args.dry_run:
        for c in conversion_list:
            shutil.rmtree(c.src)

    for src in locations:
        rename_file(src, dry_run=args.dry_run)

if __name__ == "__main__":
    main()

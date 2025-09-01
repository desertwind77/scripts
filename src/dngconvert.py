#!/usr/bin/env uv run --project /Users/athichart/Workspace/scripts
# exiftool
# brew install freetype imagemagick

import argparse
import asyncio
from pydngconverter import DNGConverter, flags

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( '-d',  '--dry-run', action='store_true',)
    parser.add_argument( "source", help="source folder")
    parser.add_argument( "destination",
                        help="destinaiton folder")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(convert_raw_to_dng(args.source, args.destination))
    loop.close()

if __name__ == "__main__":
    main()

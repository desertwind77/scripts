#!/usr/bin/env -S uv run --script --project /Users/athichart/Workspace/github/scripts/src
#!/usr/bin/env python3

from pathlib import Path
import argparse
import math
import random
import sys

# pylint: disable=import-error
from PIL import Image, ImageChops
import numpy as np

class GridInfo:
    '''Grid information'''
    def __init__(self, image_width: int, image_height: int,
                 num_horizontal_grids: int, num_vertical_grids: int) -> None:
        self.image_width = image_width
        self.image_height = image_height
        self.num_horizontal_grids = num_horizontal_grids
        self.num_vertical_grids = num_vertical_grids
        self.grid_width = image_width // num_horizontal_grids
        self.grid_height = image_height // num_vertical_grids

# Flag to enable debugging
DEBUG_ENABLED = True

def debug(txt):
    '''Print debug message'''
    if not DEBUG_ENABLED:
        return
    print(txt)

def parse_argument():
    '''Parse the command line arguments'''
    default_grid = (64, 64)
    parser = argparse.ArgumentParser(description='Create a photomasaic')
    parser.add_argument('-g', '--grid', nargs=2, default=default_grid,
                        help='number of grids in (width, height). '
                        'The default value is (64, 64)')
    parser.add_argument('-o', '--output', default='mosaic_output.png',
                        help='output image')
    parser.add_argument('-s', '--show', action='store_true',
                        help='show the final image')
    parser.add_argument('target', help='target image')
    parser.add_argument('source', help='source folder for the input images')
    return parser.parse_args()

def load_image(filename: str) -> Image:
    '''Load the target image

    Parameters:
        filename (str): the location of the target image

    Return:
        A Pillow image of the target image
    '''
    try:
        debug(f'Loading target {filename}')
        image = Image.open(filename)
    except FileNotFoundError:
        print(f'Unable to get source images from {filename}')
        sys.exit(1)
    return image

def get_grid_info(image: Image, num_horizontal_grids: int,
                  num_vertical_grids: int) -> GridInfo:
    '''Find out the information of a grid once we split the target image

    Parameters:
        image (Image): pillow Image object to be split
        horizontal_grid (int): number of horizontal grids
        vertical_grid (int): number of vertical grids

    Return:
        a Grid object containing the information of a grid
    '''
    return GridInfo(image.size[0], image.size[1], num_horizontal_grids,
                    num_vertical_grids)

def load_source_image_folder(source: str) -> list[Image]:
    '''Get the source images to be used to create a mosaic

    Parameters:
        target_image (Image): the target image
        source (str): the folder that contains the source images

    Return:
        A list of pillow Images object of the source images or None
    '''
    debug(f'Loading source {source}')

    result = []
    source_image_path = Path(source)
    for file in source_image_path.glob('**/*.jpg'):
        try:
            with open(file, 'rb') as f:
                # Open and load the image into memory
                image = Image.open(f)
                image.load()
                result.append(image)
        except KeyboardInterrupt:
            # If the number of images in the folder is huge, this function may
            # take too long. Let's exit the program gracefully.
            print('Keyboard interrupt')
            sys.exit(1)
    return result

def create_background_image(source_image_list: list[Image],
                            grid_info: GridInfo) -> Image:
    '''Combine grid of images to an image

    Parameters:
        source_image_list(list[Image]): source images in PILLOW objects
        grid_info (GridInfo): information of the grids

    Return:
        A mosaic image constructed from the source images
    '''
    # Shuffle the source images so that each run returns a different output
    random.shuffle(source_image_list)

    # Resize the source images
    debug('Resize the source images')
    for image in source_image_list:
        # TODO: handle different image size better
        image.thumbnail((grid_info.grid_width, grid_info.grid_height))

    num_source_images = len(source_image_list)
    total_grids = grid_info.num_horizontal_grids * grid_info.num_vertical_grids
    source_image_indexes = []

    cur_index = 0
    for _ in range(total_grids):
        source_image_indexes.append(cur_index)
        cur_index = (cur_index + 1) % num_source_images

    source_image_tiles = [source_image_list[i] for i in source_image_indexes]

    mosaic_image = Image.new('RGB', (grid_info.image_width, grid_info.image_height))

    for index, tile in enumerate(source_image_tiles):
        row = index // grid_info.num_horizontal_grids
        col = index - (row * grid_info.num_vertical_grids)
        mosaic_image.paste(tile, (col*grid_info.grid_width,
                                  row*grid_info.grid_height))

    return mosaic_image

def create_and_save_mosaic_image(target_image: Image, background_image: Image,
                                 output_filename: str) -> Image:
    '''Create and save the final mosaic image

    Argument:
        target_image (Image): the target image
        background_image (Image): the mosaic image created from source images
        output_filename (str): the name of the output file
    '''
    # Create a mosaic image by blending the image in the soft light mode
    output_image = ImageChops.soft_light(target_image, background_image)
    output_image.save(output_filename, 'PNG')
    return output_image

def main():
    '''The main program'''
    args = parse_argument()
    # Reference image
    target_image_name = args.target
    # Source images for the mosaic
    source_image_dir = args.source
    # The output image
    output_filename = args.output

    # Load the target image to a pillow image
    target_image = load_image(target_image_name)

    # Find out the information of a grid once we split the target image
    grid_info = get_grid_info(image=target_image,
                              num_horizontal_grids=int(args.grid[0]),
                              num_vertical_grids=int(args.grid[1]))

    # Load all the source images into pillow objects
    source_image_list = load_source_image_folder(source_image_dir)

    # Construct a mosaic background image
    background_image = create_background_image(source_image_list, grid_info)

    # Create and save the final output image
    final_image = create_and_save_mosaic_image(target_image, background_image,
                                               output_filename)
    if args.show:
        final_image.show()

if __name__ == '__main__':
    main()

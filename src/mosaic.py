#!/usr/bin/env -S uv run --script --project /Users/athichart/Workspace/github/scripts/src
#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path
import argparse
import math
import random

# pylint: disable=import-error
from PIL import Image
import numpy as np

@dataclass(frozen=True)
class Grid:
    '''Number of horizontal and vertical grids'''
    width: int
    height: int

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
                        help='number of grids (width, height)')
    parser.add_argument('-o', '--output', default='mosaic_output.png',
                        help='output image')
    parser.add_argument('target', help='target image')
    parser.add_argument('source', help='source folder for the input images')
    return parser.parse_args()

def load_target_image(target: str) -> Image:
    '''Load the target image

    Parameters:
        target (str): the location of the target image

    Return:
        A Pillow image of the target image
    '''
    debug(f'Loading target {target}')
    return Image.open(target)

def load_source_images(target_image: Image, source: str) -> list[Image]:
    '''Get the source images to be used to create a mosaic

    Parameters:
        target_image (Image): the target image
        source (str): the folder that contains the source images

    Return:
        A list of pillow Images object of the source images or None
    '''
    debug(f'Loading source {source}')

    def has_same_dimension(img1, img2):
        if (img1.size[0] == img1.size[1]) and (img2.size[0] == img2.size[1]):
            return True
        if (img1.size[0] > img1.size[1]) and (img2.size[0] > img2.size[1]):
            return True
        if (img1.size[0] < img1.size[1]) and (img2.size[0] < img2.size[1]):
            return True
        return False

    result = []
    source_image_path = Path(source)
    for file in source_image_path.glob('**/*.jpg'):
        try:
            with open(file, 'rb') as f:
                image = Image.open(f)
                image.load()
                if not has_same_dimension(target_image, image):
                    continue
                result.append(image)
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            return []
        except:
            print(f'Unable to open file {file}')

    # Shuffle the images so that each run returns a different output
    random.shuffle(result)

    return result

def resize_source_images(target_image, grid, source_images) -> None:
    '''Resize the source images

    Parameters:
        target_image:
        grid: tu
        source_images: list of pillow Images
    '''
    debug('Resize the source images')
    width = int(target_image.size[0] / grid.width)
    height = int(target_image.size[1] / grid.height)
    for image in source_images:
        image.thumbnail((width, height))

def split_target_image(target_image: Image, grid: Grid) -> list[Image]:
    '''Split the target image into grids

    Parameters:
        taget_image (Image): the image to be Split
        gird (Grid): the number of horizontal and vertical grids

    Returns:
        A list containing grids of the target image
    '''
    debug('Split the target image')
    width = int( target_image.size[0] / grid.width )
    height = int( target_image.size[1] / grid.height )

    result = []
    for j in range(grid.height):
        for i in range(grid.width):
            result.append(target_image.crop((i*width, j*height,
                                            (i+1)*width, (j+1)*height)))
    return result

def get_average_rgb(image):
    '''Get the average color of an image

    Parameters:
        image (Image): the image to be processed

    Return:
        A vector of RGB which is the average color of the image
    '''
    img = np.array(image)
    w, h, d = img.shape
    return tuple(np.average(img.reshape(w*h, d), axis=0))

def find_average_rgb(images: list[Image]) -> list[tuple]:
    '''Find average color vectors of all images in the list

    Parameters:
        images (list[Image]): list of images

    Return:
        A list of tuples, each of which represents an average RGB color of an
        image.
    '''
    return [ get_average_rgb( i ) for i in images ]

def find_closet_match_index(source_average_rgb: list[tuple],
                            target_average_rgb: list[tuple]) -> list[int]:
    '''Find the closet match between images in the source images and each tile in the target image

    Parameters:
        source_average_rgb (list[tpule]): a list of tuples, each of which
            represents an average RGB color of a source image.
        target_average_rgb (list[tpule]): a list of tuples, each of which
            represents an average RGB color of a grid of the target image.

    Return:
        A list of integer which is the index in the source images that matches the same grid index
        in the target image.
    '''
    print('Find the closet match indices', end='')

    result = []
    size = len(target_average_rgb)
    batch_size = int(size/10)

    for index, target in enumerate(target_average_rgb):
        if index % batch_size == 0:
            print('.', end='')

        min_index, min_distance = 0, float('inf')
        for index, src in enumerate(source_average_rgb):
            distance = math.pow(src[0] - target[0], 2) + \
                       math.pow(src[1] - target[1], 2) + \
                       math.pow(src[2] - target[2], 2)
            if min_distance > distance:
                min_distance = distance
                min_index = index
        result.append(min_index)

    print()

    return result

def create_image_from_tiles(tiles: list[Image], grid: Grid) -> Image:
    '''Combine grid of images to an image

    Parameters:
        tiles (list[Image]): grid of images
        grid (Grid): number of horizontal and vertical grids

    Return:
        An image constructed from the grid
    '''
    assert grid.width * grid.height == len(tiles)

    # To be on the safe side, find the max width and height of images
    width = max(i.size[0] for i in tiles)
    height = max(i.size[1] for i in tiles)

    mosaic_image = Image.new('RGB', (grid.width*width, grid.height*height))

    for index, tile in enumerate(tiles):
        row = int(index/grid.width)
        col = index - grid.height*row
        mosaic_image.paste(tile, (col*width, row*height))

    return mosaic_image

def main():
    '''The main program'''
    args = parse_argument()
    # Reference image
    target = args.target
    # Source images for the mosaic
    source = args.source
    # The output image
    output_file = args.output
    # This stores the number of horizon and vertical grids.
    grid = Grid(int(args.grid[0]), int(args.grid[1]))

    # Load the target image to a pillow image
    target_image = load_target_image(target)
    if not target_image:
        print(f'Unable to get the target image {target}')
        return

    # Load all the source images into pillow objects
    source_images = load_source_images(target_image, source)
    if not source_images:
        print(f'Unable to get source images from {source}')
        return

    # Resize each source images
    resize_source_images(target_image, grid, source_images)
    # Represent a source image with a vector whic is represented by the average
    # color of the image.
    source_average_rgb = find_average_rgb(source_images)

    # Split the target image into grids
    target_image_tiles = split_target_image(target_image, grid)
    # Represent a target image with a vector whic is represented by the average
    # color of the image.
    target_average_rgb = find_average_rgb(target_image_tiles)

    # Find the closet source image that matches for each tile in the target image
    match_index = find_closet_match_index(source_average_rgb,
                                          target_average_rgb)
    match_tiles = [source_images[i] for i in match_index]

    # Replace each tile in the target image with the closet match
    output_image = create_image_from_tiles(match_tiles, grid)
    # Write the output file
    output_image.save(output_file, 'PNG')

if __name__ == '__main__':
    main()

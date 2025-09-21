#!/usr/bin/env python3
'''A script to generate a mosaic photo'''
#
# For the sake of convenience, We can use the following command to invoke uv run.
#!/usr/bin/env -S uv run --script --project /Users/athichart/Workspace/github/scripts/src
#
# TODO:
# 1) add more background arrangements
#    - Fill background with black and randomly rotate the source image tiles a
#      few degress to the left or to the right
#    - Use different tile sizes for the background

from pathlib import Path
import argparse
import math
import os
import random
import sys
import time

# pylint: disable=import-error
from PIL import Image, ImageChops, ImageEnhance, ImageFile
from loguru import logger

EXPERIMENTAL = False

class MosaicGenerator:
    '''Create a mosaic image'''
    def __init__(self, target_image_file: str, source_image_dir: str, grid: int) -> None:
        self.target_image_file = target_image_file
        self.source_image_dir = source_image_dir
        self.grid = grid

        self.target_image = self.load_image(self.target_image_file)
        self.image_width = self.target_image.size[0]
        self.image_height = self.target_image.size[1]
        self.grid_size = min(self.image_width, self.image_height) // grid
        self.num_column = math.ceil(self.image_width/self.grid_size)
        self.num_row = math.ceil(self.image_height/self.grid_size)

    def print_summary(self):
        '''Print detail of the task'''
        target_img = Path(self.target_image_file)
        src_folder = Path(self.source_image_dir)
        logger.info(f'target image: {target_img.absolute()}')
        logger.info(f'dimensions: {self.image_width, self.image_height}')
        logger.info(f'source folder: {src_folder.absolute()}')
        logger.info(f'grid size: {self.grid_size}')
        logger.info(f'num grids: {self.num_column, self.num_row}')

    def load_image(self, filename: str) -> ImageFile.ImageFile:
        '''Load an image file'''
        logger.debug(f'Loading {filename}')
        try:
            image = Image.open(filename)
        except FileNotFoundError:
            logger.error(f'Unable to open {filename}')
            sys.exit(1)
        return image

    def load_source_image_folder(self) -> list[Path]:
        '''Load source images to be used as the background image'''
        logger.debug(f'Loading source images from {self.source_image_dir}')
        source_image_path = Path(self.source_image_dir)
        return list(source_image_path.glob('**/*.jpg'))

    def resize_source_images(self) -> list[ImageFile.ImageFile]:
        '''Crop and resize the images in the list to a square'''
        logger.debug('Resizing the source images')

        source_image_path = Path(self.source_image_dir)

        cropped_image_list = []
        for filename in source_image_path.glob('**/*.jpg'):
            image = self.load_image(str(filename))
            image.load()
            square_size = min(image.size[0], image.size[1])

            # Crop in the middle of the image
            if image.size[0] > image.size[1]:
                # Landscape orientation
                offset = (image.size[0] - square_size) // 2
                crop_box = (offset, 0, square_size + offset, square_size)
            else:
                # Portrait orientation
                offset = (image.size[1] - square_size) // 2
                crop_box = (0, offset, square_size, square_size + offset)

            new_size = (self.grid_size, self.grid_size)
            tmp_image = image.crop(crop_box)
            tmp_image = tmp_image.resize(new_size)
            cropped_image_list.append(tmp_image)
        return cropped_image_list

    def reduce_image_opacity(self, image: Image.Image,
                             opacity_percentage: int) -> Image.Image:
        '''Reduce the opacity of an image'''
        logger.debug(f'Adjust the opacity to {opacity_percentage}')
        opacity = opacity_percentage / 100.0
        rgba_img = image.convert('RGBA')
        # red, green, blue, alpha
        _, _, _, alpha = rgba_img.split()
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        rgba_img.putalpha(alpha)
        return rgba_img.convert('RGB')

    def adjust_image_brightness(self, image: Image.Image,
                                brightness_factor: float) -> Image.Image:
        '''Adjust the brightness of an image. At brightness factor 1.5, the
        image will be 50% brighter.'''
        logger.debug(f'Adjust the brightness level to {brightness_factor}')
        enhancer = ImageEnhance.Brightness(image)
        enhanced_image = enhancer.enhance(brightness_factor)
        return enhanced_image

    def create_background_image(self) -> Image.Image:
        '''Create the background image'''
        logger.debug('Creating the background image')
        # Crop and resize the source images into squares
        cropped_image_list = self.resize_source_images()
        # Shuffle the source images so that each run returns a different output
        random.shuffle(cropped_image_list)
        # Create the background image list
        num_src_img = len(cropped_image_list)
        num_grids = self.num_column * self.num_row
        img_indexes = [i % num_src_img for i in range(num_grids)]
        background_image_list = [cropped_image_list[i] for i in img_indexes]
        # Create an empty image to store the final mosaic image
        mosaic_image = Image.new('RGB', (self.image_width, self.image_height))
        # Copy the background images onto each grid in the mosaic image
        for index, tile in enumerate(background_image_list):
            row = index // self.num_column
            col = index - (row * self.num_column)
            mosaic_image.paste(tile, (col * self.grid_size,
                                      row * self.grid_size))
        return mosaic_image

    def create_mosaic(self, output_filename: str,
                      opacity_percentage: int = 100,
                      brightness_factor: float = 1.0) -> Image.Image:
        '''Create the final mosaic image'''
        self.print_summary()
        background_image = self.create_background_image()
        if EXPERIMENTAL:
            background_image = self.reduce_image_opacity(background_image,
                                                         opacity_percentage)
            background_image = self.adjust_image_brightness(background_image,
                                                            brightness_factor)

        logger.debug(f'Creating {output_filename}')
        output_image = ImageChops.soft_light(self.target_image, background_image)
        return output_image

def validate_range(value_str: str, min_val: float | None = None,
                   max_val: float | None = None) -> float:
    '''Validate that value is between min_val and max_val (inclusive)'''
    try:
        value = float(value_str)
    except ValueError as exc:
        msg = f"'{value_str}' is not a valid integer."
        raise argparse.ArgumentTypeError(msg) from exc
    min_value = -math.inf if min_val is None else min_val
    max_value = math.inf if max_val is None else max_val
    if not min_value <= value <= max_value:
        msg = f'Value must be between [{min_val}, {max_val}]'
        raise argparse.ArgumentTypeError(msg)
    return value

def parse_argument():
    '''Parse the command line arguments'''
    parser = argparse.ArgumentParser(description='Create a photomasaic')
    parser.add_argument('-B', '--brightness', action='store', default=1,
                        type=lambda x: validate_range(x, 0.1, 2),
                        help='Opacity of the background image (experiment)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print debug messages')
    parser.add_argument('-g', '--grid', default=64,
                        # Set the minimum number of grids to 16
                        type=lambda x: validate_range(x, 16 ),
                        help='number of grids on the shorter side of '
                        'the target image (default=64).')
    parser.add_argument('-O', '--opacity', action='store', default=100,
                        type=lambda x: validate_range(x, 0, 100),
                        help='Opacity of the background image (experiment)')
    parser.add_argument('-o', '--output', default='mosaic_output.png',
                        help='output image')
    parser.add_argument('-s', '--show', action='store_true',
                        help='show the final image')
    parser.add_argument('target', help='target image')
    parser.add_argument('source', help='source folder for the input images')
    return parser.parse_args()

def main():
    '''The main program'''
    args = parse_argument()
    brightness = int(args.brightness)
    grid = int(args.grid)
    opacity = int(args.opacity)
    output_filename = args.output
    source_image_dir = args.source
    target_image_name = args.target

    # Determine the output format from the output file extension
    _, file_extension = os.path.splitext(output_filename)
    print(file_extension)
    output_format = None
    if file_extension == '.png':
        output_format = 'PNG'
    elif file_extension in [ '.jpg', '.jpeg' ]:
        output_format = 'JPEG'
    else:
        logger.error(f'Unsupported output format {file_extension}')
        sys.exit(1)

    if not args.debug:
        logger.disable('')

    mosaic = MosaicGenerator(target_image_name, source_image_dir, grid)
    try:
        # Generate and save a mosaic image
        start_time = time.perf_counter()
        final_image = mosaic.create_mosaic(output_filename, opacity, brightness)
        end_time = time.perf_counter()
        final_image.save(output_filename, format=output_format)
    except KeyboardInterrupt:
        # Exit gracefully once Ctrl-c is pressed.
        logger.error('Aborted')
        sys.exit(1)

    elapsed_time = end_time - start_time
    logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

    if args.show:
        # Show the image on the screen
        final_image.show()

if __name__ == '__main__':
    main()

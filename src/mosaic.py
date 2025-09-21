#!/usr/bin/env -S uv run --script --project /Users/athichart/Workspace/github/scripts/src
#!/usr/bin/env python3

# TODO:
# 1) add more background arrangements
# 2) Using face detection during crop to ensure that the faces are in the middle

from pathlib import Path
import argparse
import math
import random
import sys

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

        self.target_image = self.load_target_image()
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

    def load_target_image(self) -> ImageFile.ImageFile:
        '''Load the target image file'''
        logger.debug(f'Loading target image {self.target_image_file}')
        try:
            image = Image.open(self.target_image_file)
        except FileNotFoundError:
            print(f'Unable to open {self.target_image_file}')
            sys.exit(1)
        return image

    def load_source_image_folder(self) -> list[ImageFile.ImageFile]:
        '''Load source images to be used as the background image'''
        logger.debug(f'Loading source images from {self.source_image_dir}')

        result = []
        source_image_path = Path(self.source_image_dir)
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

    def resize_source_images(self, images) -> list[ImageFile.ImageFile]:
        '''Crop and resize the images in the list to a square'''
        logger.debug('Resizing the source images')
        cropped_image_list = []
        for image in images:
            image_size = min(image.size[0], image.size[1])
            crop_box = (0, 0, image_size, image_size)
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
        # Load source images to be used as the background image
        source_images = self.load_source_image_folder()
        # Shuffle the source images so that each run returns a different output
        random.shuffle(source_images)

        logger.debug('Creating the background image')

        # Crop and resize the source images into squares
        cropped_image_list = self.resize_source_images(source_images)
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
        output_image.save(output_filename, 'PNG')
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
                        help='Opacity of the background image')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print debug messages')
    parser.add_argument('-g', '--grid', default=64,
                        # Set the minimum number of grids to 16
                        type=lambda x: validate_range(x, 16 ),
                        help='number of grids on the shorter side of '
                        'the target image (default=64).')
    parser.add_argument('-O', '--opacity', action='store', default=100,
                        type=lambda x: validate_range(x, 0, 100),
                        help='Opacity of the background image')
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
    grid = int(args.grid)
    opacity = int(args.opacity)
    brightness = int(args.brightness)
    target_image_name = args.target
    source_image_dir = args.source
    output_filename = args.output

    if not args.debug:
        logger.disable('')

    mosaic = MosaicGenerator(target_image_name, source_image_dir, grid)
    final_image = mosaic.create_mosaic(output_filename, opacity, brightness)

    if args.show:
        final_image.show()

if __name__ == '__main__':
    main()

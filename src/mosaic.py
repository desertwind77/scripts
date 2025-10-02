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
from PIL import Image, ImageChops, ImageEnhance
from loguru import logger

class MosaicGenerator:
    '''Create a mosaic image'''
    IMAGE_PATTERNS = ('**/*.jpg', '**/*.jpeg', '**/*.png', '**/*.webp')

    def __init__(self, target_image_file: str, source_image_dir: str,
                 tiles_on_short_side: int) -> None:
        self.target_image_file = target_image_file
        self.source_image_dir = source_image_dir
        self.tiles_on_short_side = tiles_on_short_side

        self.target_image = self.load_image(self.target_image_file)
        self.image_width = self.target_image.size[0]
        self.image_height = self.target_image.size[1]
        self.grid_size = \
                min(self.image_width, self.image_height) // tiles_on_short_side
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
        logger.info(f'num tiles: {self.num_column, self.num_row}')

    def load_image(self, filename: str) -> Image.Image:
        '''Load an image file'''
        logger.debug(f'Loading {filename}')
        try:
            image = Image.open(filename)
        except FileNotFoundError as e:
            raise FileNotFoundError(f'Unable to open {filename}') from e
        return image

    def _iter_source_paths(self):
        p = Path(self.source_image_dir)
        for pattern in self.IMAGE_PATTERNS:
            yield from p.glob(pattern)

    def resize_source_images(self) -> list[Image.Image]:
        '''Crop and resize the images in the list to a square'''
        logger.debug('Resizing the source images')

        tiles = []
        for filename in self._iter_source_paths():
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
            # Use LANCZOS Resampling for better quality
            tmp_image = tmp_image.resize(new_size, Image.Resampling.LANCZOS)
            tmp_image = tmp_image.convert('RGB')
            tiles.append(tmp_image)
        return tiles

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
        '''Adjust the brightness of an image. At the brightness factor of 1.5,
        the image is 50% brighter.'''
        logger.debug(f'Adjust the brightness level to {brightness_factor}')
        enhancer = ImageEnhance.Brightness(image)
        enhanced_image = enhancer.enhance(brightness_factor)
        return enhanced_image

    def create_background_image(self, debug: bool = False) -> Image.Image:
        '''Create the background image'''
        logger.debug('Creating the background image')

        num_grids = self.num_column * self.num_row

        # Crop and resize the source images into squares
        all_tiles = self.resize_source_images()
        if len(all_tiles) >= num_grids:
            background_image_list = random.sample(all_tiles, k=num_grids)
        else:
            background_image_list = \
                    [all_tiles[i % len(all_tiles)] for i in range(num_grids)]
        # Shuffle the source images so that each run returns a different output
        random.shuffle(background_image_list)

        # Create an empty image to store the final mosaic image
        mosaic_image = Image.new('RGB', (self.image_width, self.image_height))

        # Copy the background images onto each tile in the mosaic image
        for index, tile in enumerate(background_image_list):
            row = index // self.num_column
            col = index - (row * self.num_column)
            # Make sure that we don't overflow the canvas.
            # This code snipplet was recommended by ChatGPT.
            x0 = col * self.grid_size
            y0 = row * self.grid_size
            x1 = min(x0 + self.grid_size, self.image_width)
            y1 = min(y0 + self.grid_size, self.image_height)
            if tile.size != (x1 - x0, y1 - y0):
                tile = tile.crop((0, 0, x1 - x0, y1 - y0))
            mosaic_image.paste(tile.convert('RGB'), (x0, y0))

        if debug:
            mosaic_image.save( 'background.png', 'PNG' )

        return mosaic_image

    def create_mosaic(self, mode: str = 'soft_light',
                      alpha: float = 0.35,
                      opacity_percentage: int = 100,
                      brightness_factor: float = 1.0,
                      debug: bool = False) -> Image.Image:
        '''Create the final mosaic image'''
        self.print_summary()
        background_image = self.create_background_image(debug=debug)

        logger.debug('Creating the photo mosaic')
        if mode == 'blend':
            output_image = Image.blend(self.target_image.convert('RGB'),
                                       background_image, alpha=alpha)
        else:
            if opacity_percentage != 100 or not math.isclose(brightness_factor, 1.0):
                background_image = \
                        self.reduce_image_opacity(background_image,
                                                  int(opacity_percentage))
                background_image = \
                        self.adjust_image_brightness(background_image,
                                                     float(brightness_factor))
            output_image = ImageChops.soft_light(self.target_image.convert('RGB'),
                                                 background_image)
        return output_image

def validate_range(value_str: str, min_val: float | None = None,
                   max_val: float | None = None) -> float:
    '''Validate that value is between min_val and max_val (inclusive)'''
    try:
        value = float(value_str)
    except ValueError as exc:
        msg = f"'{value_str}' is not a valid number."
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
    parser.add_argument('--alpha', type=float, default=0.35,
                        help='The alpha parameter (for blend mode only).')
    parser.add_argument('-B', '--brightness', action='store', default=1,
                        type=lambda x: validate_range(x, 0.1, 2),
                        help='Brightness factor of the background '
                        '(experiment, 0.1-2, default=1.0)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print debug messages')
    parser.add_argument('-m','--mode', choices=['soft_light','blend'],
                        default='soft_light',
                        help='Choose the blending mode for the target image '
                        'and the background image')
    parser.add_argument('-O', '--opacity', action='store', default=100,
                        type=lambda x: validate_range(x, 0, 100),
                        help='Opacity of the background image (experiment)')
    parser.add_argument('-o', '--output', default='mosaic_output.png',
                        help='output image')
    parser.add_argument('--seed', type=int,
                        help='Random seed for reproducible layout')
    parser.add_argument('--show', action='store_true',
                        help='show the final image')
    parser.add_argument('--tiles', default=64,
                        # Set the minimum number of tiles to 16
                        type=lambda x: validate_range(x, 16 ),
                        help='number of tiles on the shorter side of '
                        'the target image (default=64).')
    parser.add_argument('-s', '---source', nargs='*', required=True,
                        help='source folder for the input images')
    parser.add_argument('-t', '--target', nargs='*', required=True,
                        help='target image')
    return parser.parse_args()

def main():
    '''The main program'''
    args = parse_argument()

    try:
        alpha = float(args.alpha)
        brightness = float(args.brightness)
        mode = args.mode
        opacity = int(args.opacity)
        output_filename = args.output
        source_image_dir = ' '.join( args.source )
        target_image_name = ' '.join( args.target )
        tiles_on_short_side = int(args.tiles)

        # Determine the output format from the output file extension
        _, file_extension = os.path.splitext(output_filename)
        ext = file_extension.lower()
        output_format = {'.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG'}.get(ext)
        if not output_format:
            raise ValueError(f'Unsupported output format {file_extension}')

        if args.seed is not None:
            random.seed(args.seed)

        if not args.debug:
            logger.remove()
            logger.add(sys.stderr, level='INFO')
        else:
            logger.remove()
            logger.add(sys.stderr, level='DEBUG')

        mosaic = MosaicGenerator(target_image_name, source_image_dir,
                                 tiles_on_short_side)

        # Generate and save a mosaic image
        start_time = time.perf_counter()
        final_image = mosaic.create_mosaic(mode, alpha, opacity, brightness,
                                           debug=args.debug)
        end_time = time.perf_counter()
        final_image.save(output_filename, format=output_format)
        elapsed_time = end_time - start_time

        logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

        if args.show:
            # Show the image on the screen
            final_image.show()
    except FileNotFoundError as e:
        logger.error(f'File not fould: {e}')
        sys.exit(1)
    except ValueError as e:
        logger.error(f'Invalid value: {e}')
        sys.exit(2)
    except KeyboardInterrupt:
        # Exit gracefully once Ctrl-c is pressed.
        logger.error('Aborted by user (Ctrl-C)')
        sys.exit(130)   # conventional exit code for SIGINT
    except Exception:
        logger.exception('Unexpected error')
        sys.exit(99)

if __name__ == '__main__':
    main()

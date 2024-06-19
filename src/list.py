#!/usr/bin/env python3
'''The script to print readme.md which is in the markdown format'''

import os
# pylint: disable=import-error
from rich.console import Console
from rich.markdown import Markdown

README_FILENAME = 'readme.md'

def main():
    '''The main function'''
    script_path = os.path.realpath( os.path.dirname( __file__ ) )
    abs_filename = os.path.join( script_path, README_FILENAME )

    text = ''
    with open( abs_filename, encoding='utf-8' ) as markdown_file:
        for line in markdown_file:
            text += line
        console = Console()
        markdown = Markdown( text )
        console.print( markdown )

if __name__ == '__main__':
    main()

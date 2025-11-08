#!/usr/bin/env python3
'''
Show a markdown file (.md)
'''

import os

# pyint: disable=import-error
from rich.console import Console
from rich.markdown import Markdown
import typer


def show_mark_down_file(filename: str):
    text = ''
    with open(filename, encoding='utf-8') as markdown_file:
        for line in markdown_file:
            text += line
        console = Console()
        markdown_text = Markdown(text)
        console.print(markdown_text)

if __name__ == '__main__':
    typer.run(show_mark_down_file)

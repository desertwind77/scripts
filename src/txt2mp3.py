#!/usr/bin/env python3
'''
Convert text files to .mp3 files
'''

from dataclasses import dataclass
import argparse
import fileinput
import os

# google text to speech library
from gtts import gTTS
import pygame


@dataclass(frozen=True)
class TextToConvert:
    '''A class to represent a text file to be converted'''
    text: str
    language: str
    output: str

    def __str__(self):
        return f'(filename: {self.output}, language: {self.language})'


def convert_text_to_speech(obj: TextToConvert) -> None:
    '''Convert text to speech using Google Text-To-Speech library

    args:
        obj (TextToConvert): the object containing text to be converted

    return:
        None
    '''
    tts = gTTS(obj.text, lang=obj.language)
    tts.save(obj.output)


def play_audio(filename: str) -> None:
    '''Play an .mp3 file
    args:
        filename (str): the .mp3 filename

    return:
        None
    '''
    print('here')
    audio = pygame.mixer.Sound(filename)
    audio.play()

    # Wait until audio finishes playing
    while pygame.mixer.get_busy():
        pygame.time.delay(10)


def convert_all_files(language: str, filenames: str, play: bool = False,
                      verbose: bool = False) -> None:
    '''Convert all input files to .mp3 files.

    args:
        language (str): the language of the input text

        filenames (str): the list of input filenames. The prefix th_ and en_
                         in the filename implies the Thai and English language,
                         respectively.

        play (bool): play and remove the converted file

        verbose (bool): print verbose message

    return:
        None
    '''
    filenames = set(sorted(filenames))

    convert_list = []
    output = text = ''
    for line in fileinput.input(filenames):
        if fileinput.isfirstline():
            # old file
            if text != '':
                # Attempt to guess the language from the filename and override
                # the language determined by argparse.
                if output.startswith('th_'):
                    language = 'th'
                elif output.startswith('en_'):
                    language = 'en'
                convert_list.append(TextToConvert(text, language, output))
                output = text = ''
            # new file
            filename = fileinput.filename()
            filename = 'stdin.txt' if filename == '<stdin>' else filename
            filename, _ = os.path.splitext(filename)
            output = f'{filename}.mp3'
        text += line
    if text != '':
        convert_list.append(TextToConvert(text, language, output))
        output = text = ''

    if play:
        pygame.mixer.init()

    # TODO: add support for parallel conversion and sequential play
    for obj in convert_list:
        if not os.path.exists(obj.output):
            if verbose:
                print(f'Converting {obj.output} ({obj.language})')
            convert_text_to_speech(obj)

        if play and os.path.exists(obj.output):
            if verbose:
                print(f'Playing {obj.output}')
            play_audio(obj.output)
            os.remove(obj.output)


def parse_arguments() -> argparse.Namespace:
    '''Parse the command line argument

    Args:
        None

    Return:
        argparse.Namespace: parsed command line arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print debug message')
    parser.add_argument('-l', '--language', action='store',
                        choices=['en', 'th'],
                        const='en', default='en', nargs="?",
                        help='Language used in the input files')
    parser.add_argument('-p', '--play', action='store_true',
                        help='Play and remove the converted .mp3 files')
    parser.add_argument('filenames', nargs="*",
                        help='Filenames to converts (default is stdin)')
    return parser.parse_args()


def main() -> None:
    '''Main function'''
    args = parse_arguments()
    convert_all_files(args.language, args.filenames, play=args.play,
                      verbose=args.verbose)


if __name__ == '__main__':
    main()

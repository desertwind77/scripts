#!/usr/bin/env python3
'''
A script to randomly print a word from the custom dictionary

TODO:
- pyest
- Continuous game
- Python GUI
- Mobile App
- Native Mac App
'''
from collections import namedtuple
import argparse
import random
import re

# pylint: disable=import-error
from colorama import Fore, Style
import yaml

from lib import check_exists, get_abs_path

CONFIG_FILENAME = 'config/vocabulary.yaml'

Pattern = namedtuple('Pattern', ['src', 'dst'])


class RegexMatchFailure(Exception):
    '''Unable to match the word in an example using the regular expression'''


class NoExampleFound(Exception):
    '''No example presents for this word's meaning'''


def load_vocabuary(filename):
    '''Load the vocabuary from a file'''
    filename = get_abs_path(__file__, filename)
    check_exists(filename, is_file=True)

    output = None
    with open(filename, 'r', encoding='utf-8') as yaml_file:
        output = yaml.safe_load(yaml_file)
    return output


def sanitize_text(txt):
    '''Clean up text e.g. removing escape characters'''
    replacement = [
        Pattern(r'\(', '('),
        Pattern(r'\)', ')'),
        Pattern('\\"', '"'),
        Pattern('\\"', '"'),
        Pattern('{', ''),
        Pattern('}', ''),
    ]
    for pattern in replacement:
        txt = txt.replace(pattern.src, pattern.dst)
    return txt


def select_words(vocab, all_words=False):
    '''Select words from the dictionary'''
    words = []
    keys = sorted(vocab.keys())
    if all_words:
        words = keys
        print(f'Dictionary size = { len( words ) } words')
    else:
        index = random.randint(0, len(keys) - 1)
        words = [keys[index]]
    return words


def print_word(vocab, words=None):
    '''Print all words in the list'''
    tab = '   '
    for word in words:
        if word not in vocab:
            continue
        print(Fore.RED + f'{sanitize_text( word )}:')
        for meaning, examples in vocab[word].items():
            print(Fore.GREEN + f'{tab}{sanitize_text( meaning ) }:')
            if not examples:
                continue
            for example in examples:
                if r'\{' in example and r'\}' in example:
                    example = example.replace(r'\{', '{')
                    example = example.replace(r'\}', '}')
                begin_index = example.find('{')
                end_index = example.find('}')
                if begin_index == -1 or end_index == -1:
                    print(Fore.CYAN + f'{tab}{tab}{sanitize_text( example ) }')
                else:
                    begin = sanitize_text(example[0: begin_index])
                    middle = sanitize_text(example[begin_index: end_index + 1])
                    end = sanitize_text(example[end_index + 1:])
                    print(f'{tab}{tab}', end='')
                    print(Fore.CYAN + f'{begin}', end='')
                    print(Fore.YELLOW + f'{middle}', end='')
                    print(Fore.CYAN + f'{end}')
    print(Style.RESET_ALL)


def game_fill_in_word(vocab):
    '''Game to fill a word in the blank'''
    def get_word(vocab):
        word, word_info = random.choice(list(vocab.items()))
        # For debugging:
        word_info = vocab[word]
        meaning = random.choice(list(word_info.keys()))
        examples = word_info[meaning]
        example = random.choice(examples) if examples else None
        return word, meaning, example

    def get_multiple_choices(vocab, word):
        # Select three multiple choices
        cindices = list(random.sample(range(0, len(vocab) - 1), 4))
        choices = [sorted(vocab.keys())[i] for i in cindices]
        if word not in choices:
            choices.append(word)
        random.shuffle(choices)
        return choices

    word, meaning, example = get_word(vocab)
    if not example:
        raise NoExampleFound(word)
    choices = get_multiple_choices(vocab, word)

    obj = re.search(r'.*({.*}).*', example)
    if not obj:
        raise RegexMatchFailure(example)
    pattern = obj.group(1)
    blank = '_' * len(pattern)
    example = example.replace(pattern, blank)
    print(f'Question : {sanitize_text( example )}\n')
    print(f'Meaning  : {sanitize_text( meaning )}\n')
    print('Answer   :')
    for choice in choices:
        print(f'* {sanitize_text( choice )}')


def process_arguments():
    '''Process the command line arguments'''
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', action='store_true',
                        help='Print all words in the dictionary')
    parser.add_argument('-g', '--game', action='store_true',
                        help='Play the game to fill in the blank')
    parser.add_argument('-s', '--search', action='store',
                        help='Search the word')
    return parser.parse_args()


def main():
    '''The main function'''
    args = process_arguments()
    vocab = load_vocabuary(CONFIG_FILENAME)

    if args.game:
        game_fill_in_word(vocab)
    elif args.search:
        print_word(vocab, [args.search])
    else:
        words = select_words(vocab, all_words=args.all)
        print_word(vocab, words)


if __name__ == '__main__':
    main()

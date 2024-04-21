#!/usr/bin/env python3
'''
A script to randomly print a word from the custom dictionary

TODO:
- Clean up the dictionary file
- Print the game statistics
- Python GUI
- Mobile App
- Native Mac App
'''
from dataclasses import dataclass
import argparse
import random
import re
import sys
# pylint: disable=import-error
from colorama import Fore, Style
import yaml


class RegexMatchFailure(Exception):
    '''Unable to match the word in an example using the regular expression'''


class NoExampleFound(Exception):
    '''No example presents for this word's meaning'''


@dataclass
class ReplacePattern:
    '''For replacing src with dst'''
    src: str
    dst: str


class Word:
    tab = '   '

    '''General base class'''
    def sanitize_text(self, txt: str) -> str:
        '''Clean up text e.g. removing escape characters

        Args:
            txt (str): the text to be cleaned up

        Returns:
            (str) the cleaned up text
        '''
        replacement = [
            ReplacePattern(r'\(', '('),
            ReplacePattern(r'\)', ')'),
            ReplacePattern('\\"', '"'),
            ReplacePattern('\\"', '"'),
            ReplacePattern('{', ''),
            ReplacePattern('}', ''),
        ]
        for pattern in replacement:
            txt = txt.replace(pattern.src, pattern.dst)
        return txt


class Game(Word):
    '''A word-filing game'''
    def __init__(self, word: str, meaning: str,
                 example: str, choices: list[str]) -> None:
        '''Constructor

        Args:
            word (str): the word and correct answer

            meaning (str): the meaning of the word

            example (str): the example sentence to be used as the question

            choices (list[str]): a list of words to be used in the
                                 multiple choices
        '''
        # Replace the word between { and } with underscores.
        example = example.replace(r'\{', '{')
        example = example.replace(r'\}', '}')
        obj = re.search(r'.*({.*}).*', example)
        if not obj:
            raise RegexMatchFailure(example)
        pattern = obj.group(1)
        example = example.replace(pattern, '_' * 5)

        self.word = self.sanitize_text(word)
        self.meaning = self.sanitize_text(meaning)
        self.example = self.sanitize_text(example)
        self.choices = [self.sanitize_text(t) for t in choices]

        letters = [chr(ord('a') + i) for i in range(len(self.choices))]
        self.multiple_choices = list(zip(letters, self.choices))
        self.answer = next(i[0] for i in self.multiple_choices
                           if i[1] == self.word)

    def print(self) -> None:
        '''Print the question, meaning and multiple choices'''
        print(f'Question : {self.example}')
        print(f'Meaning  : {self.meaning}')
        for choice in self.multiple_choices:
            print(f'{self.tab}{choice[0]}) {choice[1]}')

    def check_answer(self, answer: str) -> bool:
        '''Check if the answer is correct

        Args:
            answer (str): the answer

        Returns:
            (bool) True if the answer is correct
        '''
        return answer == self.answer


class Dictionary(Word):
    '''The class representing the dictionary'''
    color_word = Fore.RED
    color_meaning = Fore.GREEN
    color_example = Fore.CYAN
    color_highlight = Fore.YELLOW
    num_multiple_choices = 4

    def __init__(self, filename: str) -> None:
        '''Constructor

        Args:
            filename (str): the dictionary file in the YAML format
        '''
        self.filename = filename
        self.dictionary = self.load_from_file()

    def size(self) -> int:
        '''Get the number of words in the dictionary

        Returns:
            (int) the number of words in the dictionary
        '''
        return 0 if self.dictionary is None else len(self.dictionary)

    def load_from_file(self) -> dict:
        '''Load the vocabuary from a YAML file and return the dictionary in the
        format of vocab -> { meaning -> list of examples }

        Args:
            filename (str) : the YAML file containing the vocabuary

        Returns:
            dictionary containing the vocabuary in the following format
        '''
        output = None
        try:
            with open(self.filename, 'r', encoding='utf-8') as yaml_file:
                output = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f'File not found: {self.filename}')
            sys.exit(1)
        return output

    def select_words(self, all_words: bool = False) -> list[str]:
        '''Randomly select a  word or all words from the dictionary for
        printing depending on the all_words flag.

        Args:
            dictionary (dict): the dictionary containing vocabularies,
                               meanings, and examples

            all_words (bool): select all the words in the dictionary

        Returns:
            list of selected words
        '''
        if all_words:
            words = sorted(self.dictionary.keys())
        else:
            words = [random.choice(list(self.dictionary.keys()))]
        return words

    def print_word(self, words: list[str] = None) -> None:
        '''Look up and print all the words in the dictionary.

        Args:
            dictionary (dict): the dictionary containing vocabularies,
                               meanings, and examples

            words (list[str]): list of words
        '''
        for word in words:
            if word not in self.dictionary:
                continue
            print(self.color_word, end='')
            print(f'{self.sanitize_text(word)}:')

            for meaning, examples in self.dictionary[word].items():
                print(self.color_meaning, end='')
                print(f'{self.tab}{self.sanitize_text(meaning) }:')

                if not examples:
                    continue

                for example in examples:
                    example = example.replace(r'\{', '{')
                    example = example.replace(r'\}', '}')

                    begin_index = example.find('{')
                    end_index = example.find('}')
                    if begin_index == -1 or end_index == -1:
                        print(self.color_example, end='')
                        example = self.sanitize_text(example)
                        print(f'{self.tab}{self.tab}{example}')
                    else:
                        begin = self.sanitize_text(example[0: begin_index])
                        middle = self.sanitize_text(
                                example[begin_index: end_index + 1])
                        end = self.sanitize_text(example[end_index + 1:])

                        print(f'{self.tab}{self.tab}', end='')
                        print(self.color_example + f'{begin}', end='')
                        print(self.color_highlight + f'{middle}', end='')
                        print(self.color_example + f'{end}')
        print(Style.RESET_ALL)

    def generate_game(self) -> Game:
        '''Generate a word-filling game'''
        # Select word, meaning, example
        word, word_info = random.choice(list(self.dictionary.items()))
        meaning, examples = random.choice(list(word_info.items()))
        if not examples:
            raise NoExampleFound(word)
        example = random.choice(examples) if examples else None

        # Generate the multiple choices
        cindices = list(random.sample(range(0, len(self.dictionary) - 1),
                                      self.num_multiple_choices + 1))
        choices = [sorted(self.dictionary.keys())[i] for i in cindices]
        if word in choices:
            choices = [c for c in choices if c != word]
        else:
            choices = choices[1:]
        choices = [*choices, word]
        random.shuffle(choices)

        return Game(word, meaning, example, choices)

    def verify(self) -> None:
        '''Verify that all meanings have at least an example'''
        need_examples = set(word
                            for word, meanings in self.dictionary.items()
                            for meaning, examples in meanings.items()
                            if examples is None)
        for word in sorted(list(need_examples)):
            self.print_word([word])

        if need_examples:
            assert False


def process_arguments() -> argparse.Namespace:
    '''Process the command line arguments

    Returns:
        (argparse.Namespace) parsed command line arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('dictionary', action='store',
                        help='The dictionary file in the YAML format')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Print all words in the dictionary')
    parser.add_argument('-g', '--game', action='store_true',
                        help='Play the game to fill in the blank')
    parser.add_argument('-s', '--search', action='store',
                        help='Search the word')
    parser.add_argument('-V', '--verify', action='store_true',
                        help='Verify the dictionary file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print debug information')
    return parser.parse_args()


def main():
    '''The main function'''
    args = process_arguments()
    dictionary = Dictionary(args.dictionary)

    if args.verify:
        dictionary.verify()
    if args.verbose:
        print(f'Dictionary size = {dictionary.size()} words')

    if args.game:
        game = dictionary.generate_game()
        game.print()

        attempt, max_attempt, new_game = 0, 2, False
        answer = input('Enter your answer or q/Q to quite:')
        while answer not in ['q', 'Q']:
            if game.check_answer(answer):
                print(Fore.GREEN + "That's correct! Congratulation" +
                      Style.RESET_ALL)
                new_game = True
            else:
                attempt += 1
                if attempt == max_attempt:
                    print(Fore.RED + "That's too bad!" + Style.RESET_ALL)
                    new_game = True
                else:
                    print(Fore.RED + "Try again!" + Style.RESET_ALL)
                    answer = input('Enter your answer or q/Q to quite:')

            if new_game:
                attempt, new_game = 0, False
                game = dictionary.generate_game()
                game.print()
                answer = input('Enter your answer or q/Q to quite:')
    else:
        words = [args.search] if args.search else \
                dictionary.select_words(all_words=args.all)
        dictionary.print_word(words)


if __name__ == '__main__':
    main()

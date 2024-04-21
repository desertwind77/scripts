#!/usr/bin/env python3
'''Test file for the vocab.py script'''

import os
import pytest
from vocab import Dictionary


@pytest.fixture()
def filename():
    '''Return the location of the dictionary file'''
    script_path = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(script_path, '../config/vocabulary.yaml')


@pytest.fixture()
def dictionary(filename):
    '''Return the dictionary object'''
    return Dictionary(filename)


def test_print_all(dictionary):
    '''Print the whole dictionary'''
    words = dictionary.select_words(all_words=True)
    dictionary.print_word(words)


def test_print_non_exist_word(dictionary):
    '''Search for a non-existent word'''
    words = ['NON_EXIST_WORD']
    dictionary.print_word(words)


def test_game_correct(dictionary):
    '''Answer a game correctly'''
    game = dictionary.generate_game()
    assert game.check_answer(game.answer)


def test_game_incorrect(dictionary):
    '''Answer a game incorrectly'''
    game = dictionary.generate_game()
    choice = next(i[0] for i in game.multiple_choices if i[1] != game.answer)
    assert not game.check_answer(choice)

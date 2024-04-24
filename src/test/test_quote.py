#!/usr/bin/env python3
'''Test file for the quote.py script'''

import os
import pytest
from quote import QuoteDB


@pytest.fixture()
def filename():
    '''Return the location of the dictionary file'''
    script_path = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(script_path, '../config/Quotes.md')


@pytest.fixture()
def quotedb(filename):
    '''Return the QuoteDB object'''
    return QuoteDB(filename)


def test_print_all(quotedb):
    '''Just print the whole quote database and see if it will crash'''
    quotedb.print_quotes()

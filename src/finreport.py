#!/usr/bin/env python3
'''Show or queyr my expense summary'''

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import argparse
import csv
import json
import os
import re

# tabulate doc : https://pypi.org/project/tabulate/
# pylint: disable=import-error
# pylint: disable=too-many-arguments
# pylint: disable=too-many-branches
from rich.console import Console
from rich.table import Table
from rich.traceback import install
from tabulate import tabulate, SEPARATING_LINE
import PyPDF2

CONFIG_FILENAME="config/finreport.json"

class MissingRegexException( Exception ):
    '''No regular expression to parse a pdf file'''
    # Currently, it is not in use because we stop parsing the .pdf
    # bank statement. The transaction format in the .pdf statemnt
    # keeps changing. It is burdensome to keep maintaining the
    # regular expression to parse these transactions.

class UnknownAccountException( Exception ):
    '''A statement doesn't match with accounts defined in the config'''

class UnknownDataTypeInConfigException( Exception ):
    '''Unknown data type found in the config (expectint str or dict)'''

class UnknownTransactionCategoryException( Exception ):
    '''Transactions with unknown categories exists'''

class  MissingTransactionException( Exception ):
    '''Some transactions in a PDF file were not recognized'''

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class Account:
    '''The class to represent an account'''
    # pylint: disable=too-many-arguments
    def __init__( self, name, enabled, filename, account_type,
                  check_regex, regex, has_year_in_date,
                  has_positive_expenses, has_header, fields ):
        self.name = name
        self.enabled = enabled
        self.filename = filename
        self.account_type = account_type
        self.check_regex = check_regex
        self.regex = regex
        self.has_year_in_date = has_year_in_date
        self.has_positive_expenses = has_positive_expenses
        self.has_header = has_header
        self.fields = fields

        if self.filename.endswith( '.pdf' ) and not self.regex:
            raise MissingRegexException( self.name )

# pylint: disable=too-few-public-methods
class Transaction:
    '''The class to represents a transaction'''
    # pylint: disable=too-many-arguments
    def __init__( self, statement, date, description, category, amount ):
        self.statement = statement
        self.date = date
        self.description = description
        self.category = category
        self.amount = amount

    def __str__( self ):
        return f'{self.date.strftime( "%m/%d/%Y")}   {self.amount}   {self.description}'

class Statement:
    '''The class to represent a credit card or a bank statement containing transactions'''
    def __init__( self, filename : str, account : str, category_info : dict):
        self.filename = filename
        self.account = account
        self.category_info = category_info
        self.transactions = []

    def get_category( self, description : str ) -> str:
        '''Get the category of a transaction

        args:
            description (str) : the description of a transaction
        '''
        account_type = self.account.account_type
        known_category = None
        for merchant, category in self.category_info[ account_type ].items():
            if re.search( merchant.lower(), description.lower() ):
                known_category = category
                break
        return known_category

    def cleanup_description( self, description : str ) -> str:
        '''Replace unwanted characters that may confuse the regular expression

        args:
            description (str) : the description of a transaction
        '''
        result = description
        for src, dst in self.category_info[ 'Replace' ].items():
            result = result.replace( src, dst )
        return result

    def load_transactions( self ):
        '''Read and categorize all transactions from a statement'''
        if not self.account.enabled:
            return
        if self.filename.endswith( 'pdf' ):
            self.load_pdf_file()
        elif self.filename.endswith( 'csv' ):
            self.load_csv_file()
        else:
            pass

    # pylint: disable=too-many-locals
    def load_csv_file( self ):
        '''Read and categorize all transactions from a .csv file'''
        field_date = self.account.fields[ 'Transaction Date' ]
        field_desc = self.account.fields[ 'SEARCH' ]
        field_amount = self.account.fields[ 'Amount' ]

        account_type = self.account.account_type
        ignored_categories = self.category_info[ 'Ignored' ][ account_type ]

        skip_header = self.account.has_header
        with open( self.filename, 'rt', encoding='utf-8' ) as file:
            reader = csv.reader( file )
            for row in reader:
                if skip_header:
                    skip_header = False
                    continue
                if not row:
                    continue
                date = datetime.strptime( row[ field_date ], '%m/%d/%Y' )
                description = self.cleanup_description( row[ field_desc ] )
                amount = row[ field_amount ].replace( '$', '' )
                modifier = 1
                obj = re.match( r'\(([0-9.]+)\)', amount )
                if obj:
                    amount = obj.group( 1 )
                    modifier = -1
                amount = modifier * round( float( amount ), 2 )
                amount = -1 * amount if self.account.has_positive_expenses else amount
                category = self.get_category( description )
                if category in ignored_categories:
                    continue
                transaction = Transaction( self, date, description, category, amount )
                self.transactions.append( transaction )

    # pylint: disable=too-many-locals
    def load_pdf_file( self ):
        '''Read and categorize all transactions from a .pdf file'''
        field_date = self.account.fields[ 'Transaction Date' ]
        field_desc = self.account.fields[ 'Description' ]
        field_amount = self.account.fields[ 'Amount' ]

        account_type = self.account.account_type
        ignored_categories = self.category_info[ 'Ignored' ][ account_type ]

        # Get the year from filename for the statements in which
        # no year in the transaction date
        file_path = Path( self.filename )
        year = str( file_path.name )[ :4 ] \
                if not self.account.has_year_in_date else None

        count = 0
        reader = PyPDF2.PdfReader( self.filename, strict=False )
        text = ''
        for page in reader.pages:
            text += page.extract_text()

        for regex in self.account.regex:
            matches = re.compile( regex, re.MULTILINE )
            for match in matches.finditer( text ):
                count += 1
                date = match.group( field_date )
                # pylint: disable=fixme
                # FIXME: assuming the date is in the format mm/dd
                date = f'{date}/{year}' if year else date
                date = datetime.strptime( date, '%m/%d/%Y' )

                description = self.cleanup_description( match.group( field_desc ) )

                amount = match.group( field_amount ).replace( ',', '' )
                amount = round( float( amount ), 2 )
                amount = -1 * amount if self.account.has_positive_expenses else amount

                category = self.get_category( description )
                if category in ignored_categories:
                    continue

                transaction = Transaction( self, date, description, category, amount )
                self.transactions.append( transaction )

        # Double check to make sure that we process all the transactions
        if self.account.check_regex:
            check_count = 0
            for line in text.splitlines():
                if re.match( self.account.check_regex, line ):
                    check_count += 1
            if count != check_count:
                raise MissingTransactionException( str( file_path.name ), count, check_count )

class CreditReport:
    '''The main class to process credit card and bank statements'''
    def __init__( self, config, statement_location ):
        self.config = config
        self.statement_location = statement_location
        self.account_info = {}
        self.category_info = {}
        self.statements = []
        self.expense_by_category = {}

    def load_account_config( self ):
        """Create an Account object whic represents an account"""
        account_config = self.config[ 'Accounts' ]
        for name, info in account_config.items():
            enabled = info[ 'Enabled' ] == 'True'
            filename = info[ 'Filename' ]
            account_type = info[ 'Type' ]
            check_regex = info.get( 'Check Regex', None )
            regex = info.get( 'Regex', None )
            has_year_in_date = info[ 'Has Transaction Year' ] == 'True'
            has_positive_expenses = info['Has Postive Expenses' ] == 'True'
            has_header = info.get( 'Header', False )
            fields = info[ 'Fields' ]
            self.account_info[ name ] = Account( name, enabled, filename, account_type,
                                                 check_regex, regex, has_year_in_date,
                                                 has_positive_expenses,
                                                 has_header, fields )

    def load_category_config( self ):
        '''Create a dictionary from 'expense' to category'''
        category_data = self.config[ 'Category' ]

        for account_type in [ "Credit Card", "Bank Account" ]:
            self.category_info[ account_type ] = {}
            account_category_data = category_data[ account_type ]
            for category, expenses in account_category_data.items():
                for expense in expenses:
                    if isinstance( expense, dict ):
                        for key in expense.keys():
                            self.category_info[ account_type ][ key ] = category
                    elif isinstance( expense, str ):
                        self.category_info[ account_type ][ expense ] = category
                    else:
                        raise UnknownDataTypeInConfigException( type( expense ) )

        self.category_info[ 'Ignored' ] = category_data[ 'Ignored' ]
        self.category_info[ 'Replace' ] = category_data[ 'Replace' ]

    def generate_statements_from_files( self ):
        '''Create a Statement object for each available statement files on the drive'''
        statement_path = Path( self.statement_location )

        statement_files = list( statement_path.glob( '*.pdf' ) )
        statement_files += list( statement_path.glob( '*.csv' ) )

        for statement_file in statement_files:
            filename = str( statement_file.name )
            statement = None
            for _, account in self.account_info.items():
                obj = re.match( account.filename, filename )
                if obj:
                    statement = Statement( str( statement_file ), account, self.category_info )
            if not statement:
                raise UnknownAccountException( str( statement_file ) )
            self.statements.append( statement )

    def calculate_expenses_by_category( self, known_categories : dict ):
        '''Calculate expenses by ( account type, category )

        args:
            known_categories (str) : a dictionary of ( account_type, categories )
        '''
        for account_type, categories in known_categories.items():
            self.expense_by_category[ account_type ] = {}
            for category in categories:
                self.expense_by_category[ account_type ][ category ] = defaultdict( float )

        for statement in self.statements:
            account_type = statement.account.account_type
            for transaction in statement.transactions:
                amount = self.expense_by_category[ account_type ] \
                        [ transaction.category ][ transaction.date.month ]
                amount += transaction.amount
                amount = round( amount, 2 )
                self.expense_by_category[ account_type ][ transaction.category ] \
                        [ transaction.date.month ] = amount

    def load_all_transactions( self, verbose : bool = False ):
        '''Load all transactions in all statements and add them to the right categories

        args:
            verbose (bool) : print the debug info
        '''
        for statement in sorted( self.statements, key=lambda x: x.filename, reverse=False ):
            statement.load_transactions()

        # See if there are any transactions without category
        unknown_transactions = []
        known_categories = defaultdict( list )
        for statement in self.statements:
            for transaction in statement.transactions:
                account_type = statement.account.account_type
                if transaction.category is None:
                    unknown_transactions.append( transaction )
                else:
                    known_categories[ account_type ].append( transaction.category )
        if unknown_transactions:
            print( 'Unknown transactions:' )
            for transaction in unknown_transactions:
                print( Path( transaction.statement.filename ).name,
                       transaction.date, transaction.description )
            raise UnknownTransactionCategoryException
        for account_type, categories in known_categories.items():
            known_categories[ account_type ] = list( set( categories ) )

        self.calculate_expenses_by_category( known_categories )

    def print_expense_summary_by_account_type( self, account_type : str,
                                               plain : bool = True ):
        '''Print the financial report where it is grouped by the account type

        args:
            account_type (str) : account type
            plain (bool) : print the output using plain text
        '''
        table = []
        for category in sorted( self.expense_by_category[ account_type ].keys() ):
            expenses = self.expense_by_category[ account_type ][ category ]
            row = [ round( expenses.get( i, 0 ) ) for i in range( 1, 13 ) ]
            total = sum( row )
            row = [ category ] + row + [ total ]
            table.append( row )
        if plain:
            table.append( SEPARATING_LINE )

        total_row = []
        for month in range( 1, 13 ):
            monthly_expenses = 0
            for category, expenses in self.expense_by_category[ account_type ].items():
                monthly_expenses += expenses.get( month, 0 )
            total_row.append( round( monthly_expenses ) )
        total = sum( total_row )
        total_row = [ 'Subtotal' ] + total_row + [ total ]
        table.append( total_row )

        headers = [ 'Category', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Total' ]
        if plain:
            print( f'[{account_type}]' )
            print( tabulate( table, headers, tablefmt="simple", intfmt="," ) )
            print()
        else:
            console = Console()
            rich_table = Table( title=f'{account_type}' )
            for header in headers:
                if header in [ 'Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov' ]:
                    rich_table.add_column( header, justify='right', style='bright_black' )
                elif header in [ 'Feb', 'Apr', 'Jun', 'Aug', 'Oct', 'Dec' ]:
                    rich_table.add_column( header, justify='right', style='white' )
                elif header == 'Total':
                    rich_table.add_column( header, justify='right', style='red' )
                else:
                    rich_table.add_column( header, style='magenta' )
            for row in table:
                row = [ r if isinstance( r, str ) else str( r ) for r in row ]
                rich_table.add_row( *row )
            console.print( rich_table )
            print()

    def print_expense_summary( self, plain : bool = False ):
        '''Print expense summary

        args:
            plain (bool) : print the output using plain text
        '''
        for account_type in sorted( self.expense_by_category.keys() ):
            self.print_expense_summary_by_account_type( account_type, plain=plain )

    def query( self, account : str = None, month : int = None,
               category : str = None, group_by_account : bool = False,
               verbose : bool = False ):
        '''Query transactions based on account, month, and category if any of these
        critria are specified.

        Args:
            account (str) : the account name to query
            month (int) : the month to query
            category (str) : the category to query
            group_by_account (bool) : group the transactions by account or not
            verbose (bool) : print the debug info or not
        '''
        if verbose:
            query_str = 'Query: '
            if account:
                query_str += f'account = {account}, '
            if month:
                query_str += f'month = {month}, '
            if category:
                query_str += f'category = {category}, '
            if group_by_account:
                query_str += 'grouping = True'
            print( query_str )
            print()

        result = defaultdict( list ) if group_by_account else []

        for statement in self.statements:
            for transaction in statement.transactions:
                if account and transaction.statement.account.name != account:
                    continue
                if month and transaction.date.month != month:
                    continue
                if category and transaction.category != category:
                    continue

                if isinstance( result, list ):
                    result.append( transaction )
                else:
                    result[ transaction.statement.account.name ].append( transaction )

        if isinstance( result, list ):
            result = sorted( result, key=lambda x: x.date )
            list( map( print, result ) )
            total = round( sum( t.amount for t in result ), 2 )
            print( f'Total = {total}' )
        elif isinstance( result, defaultdict ):
            for account_name, expenses in result.items():
                print( account_name )
                expenses = sorted( expenses, key=lambda x: x.date )
                list( map( print, expenses ) )
                total = round( sum( t.amount for t in expenses ), 2 )
                print( f'Total = {total}' )
                print()

    def run( self, account : str = None, month : int = None,
             category : str = None, group_by_account : bool = False,
             plain : bool = False, verbose : bool = False ):
        '''This function has two use cases.

        1. Print the financial summary for all the statements in a year.

        2. Query transactions based on account, month, and category if
           any of these critria are specified.

        Args:
            account (str) : the account name to query
            month (int) : the month to query
            category (str) : the category to query
            group_by_account (bool) : group the transactions by account or not
            plain (bool) : print the output using plain text
            verbose (bool) : print the debug info or not
        '''
        self.load_account_config()
        self.load_category_config()
        self.generate_statements_from_files()
        self.load_all_transactions( verbose=verbose )
        if not any( [ account, month, category ] ):
            self.print_expense_summary( plain=plain )
        else:
            self.query( account=account, month=month, category=category,
                        group_by_account=group_by_account,
                        verbose=verbose )

def process_command_line_arguments( config : dict ) -> argparse.Namespace:
    '''Process command line arguments

    args:
        config : the configuration dictionary. This is loaded from a JSON file

    return:
        a parsed argparse namespace
    '''
    accounts = config[ 'Accounts' ].keys()
    category = []
    for key, value in config[ 'Category' ].items():
        if key in [ 'Ignored', 'Replace' ]:
            continue
        category += value.keys()

    parser = argparse.ArgumentParser()
    parser.add_argument( "-a", "--account", action='store', choices=accounts,
                         help="Account of interest" )
    parser.add_argument( "-c", "--category", action='store', choices=category,
                         help="Category of interest" )
    parser.add_argument( "-g", "--group", action='store_true',
                         help="Group transactions by account" )
    parser.add_argument( "-l", "--location", required=True, action='store',
                         dest='location', help="Locaiton of the statement files" )
    parser.add_argument( "-m", "--month", action='store',
                         help="Month of interest" )
    parser.add_argument( "-y", "--year", action='store',
                         help="Year of interest" )
    parser.add_argument( "-p", "--plain", action="store_true",
                         help="Print the output using plain text" )
    parser.add_argument( "-v", "--verbose", action="store_true",
                         help="Print more information" )
    return parser.parse_args()

def load_config( config_filename : str, verbose : bool = False ) -> dict:
    '''Load the configuration stored in a JSON file. The configuration must
    be stored with the key 'config'.

    args:
        config_filename (str) : the JSON file storing the configuration
        verbose (bool) : print the debug information or not

    returns:
        a dictionary containing the configuration
    '''
    # __file__ stores the absolute path of the python script
    # realpath() return the canonical path of the specified
    # filename by eliminating any symbolic links encountered
    # in the path
    script_path = os.path.realpath( os.path.dirname( __file__ ) )
    config_abs_filename = os.path.join( script_path, config_filename )

    config = None
    with open( config_abs_filename, encoding="utf-8" ) as config_file:
        if verbose:
            print( f'Loading config file: {config_abs_filename}' )
        config_data = json.load( config_file )
        config = config_data.get( 'config', None )
    return config


def main():
    '''The main program'''
    # Install rich traceback to override the default python traceback
    install()

    config = load_config( CONFIG_FILENAME )
    args = process_command_line_arguments( config )
    account = args.account
    category = args.category
    group = args.group
    month = int( args.month ) if args.month else None
    year = args.year if args.year else datetime.now().year
    plain = args.plain
    verbose = args.verbose
    location = str( Path( args.location )/str( year ) )
    if not os.path.exists( location ):
        print( f'{location} does not exist' )
        return

    reporter = CreditReport( config, location )
    reporter.run( account=account, month=month, category=category,
                  group_by_account=group, plain=plain, verbose=verbose )

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
'''Rename rom files and also remove duplicated files'''

import argparse
import hashlib
import os
import re

def remove_translated( text ):
    '''Remove (translated .*)'''
    pattern = r'(.*) \(Translated.*\)(.*)'
    obj = re.match( pattern, text )
    if obj:
        text = obj.group( 1 ) + obj.group( 2 )
    return text

def remove_area_codes( text ):
    '''Remove the area code e.g. Blah Blah (USA).ext'''
    for area in [ 'J', 'Ch', 'USA', 'Europe' , 'Japan' ]:
        # pylint: disable=anomalous-backslash-in-string
        pattern = f'(.*) \({area}\)(.*)'
        obj = re.match( pattern, text )
        if obj:
            text = obj.group( 1 ) + obj.group( 2 )
            return text
    return text

def remove_parenthesis( text ):
    '''Remove the parenthesises'''
    obj = re.match( r'(.*) \(.*\)(.*)', text )
    if obj:
        text = obj.group( 1 ) + obj.group( 2 )

    obj = re.match( r'(.*) \[.*\](.*)', text )
    if obj:
        text = obj.group( 1 ) + obj.group( 2 )

    return text

def remove_tailing_the( text ):
    '''Remove the tailing 'the' e.g. Blah Blah, The.ext'''
    # if text.endswith( ', The' ):
    #     text = 'The ' + text[ :-5 ]
    obj = re.match( r'(.*), The(.*)', text )
    if obj:
        text = 'The ' + obj.group( 1 ) + obj.group( 2 )
    return text

MD5DB = {}
def remove_duplicated_file( rom ):
    '''Remove duplicated files using md5 checksum'''
    # pylint: disable=global-variable-not-assigned
    global MD5DB

    # pylint: disable=consider-using-with
    chksum = hashlib.md5( open( rom, 'rb' ).read() ).hexdigest()
    if chksum in MD5DB:
        original = MD5DB[ chksum ]
        print( f'Removing {rom} duplicated with {original}' )
        os.remove( rom )
        return True

    MD5DB[ chksum ] = rom
    return False

def main():
    '''The main function'''
    parser = argparse.ArgumentParser( description='Rename rom files' )
    parser.add_argument( '-d', '--dryRun', action='store_true',
                        dest='dry_run', help='Dry run' )
    parser.add_argument( '-v', '--verbose', action='store_true',
                        dest='verbose', help='Print detail' )
    parser.add_argument( '-c', '--checksum', action='store_true',
                        dest='checksum',
                        help='Remove duplicated files using checksum' )
    parser.add_argument( 'folder', action='store', help='Rom folder' )
    args = parser.parse_args()

    current_dir = os.getcwd()
    os.chdir( args.folder )

    for rom in sorted( os.listdir( '.' ) ):
        if rom == '.DS_Store':
            continue

        # Renaming the rom file
        filename, ext = os.path.splitext( rom )
        filename = remove_translated( filename )
        filename = remove_area_codes( filename )
        filename = remove_parenthesis( filename )
        filename = remove_tailing_the( filename )
        fullname = filename + ext.lower()

        if args.dry_run:
            print( f'Renaming {rom} to {fullname}' )
            continue

        if args.verbose:
            print( fullname )
        os.rename( rom, fullname )

        if args.checksum:
            remove_duplicated_file( fullname )

    os.chdir( current_dir )

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
'''
Copy photo from the working directory to portfolio, google drive
'''

from collections import defaultdict
from pathlib import Path
import argparse
import os
import re
import shutil
import sys
# pylint: disable=import-error
import iptcinfo3
# pylint: disable=import-error
from PIL import Image
from genutils import ( FileNotFound,
                       DirectoryNotFound,
                       load_config,
                       check_if_folder_exists )

CONFIG_FILE = 'config/portmgr.json'

class SourceFileNotFound( Exception ):
    """Raised when a source file is missing from one of the config[ 'SourceSubfolders' ]"""
    def __init__( self, location, src_file ):
        self.location = location
        self.src_file = src_file
        message = f'{self.location} is missing from {self.src_file}'
        super().__init__( message )

class PortfolioMismatchException( Exception ):
    '''Raised when the contents of subfolders, e.g. Full, PSD, Web, in the portfolio
    don't match'''
    def __init__( self, portfolio, folder1, filelist1, folder2, filelist2 ):
        self.portfolio = portfolio
        self.folder1 = folder1
        self.filelist1 = filelist1
        self.folder2 = folder2
        self.filelist2 = filelist2

    def __str__( self ):
        list1 = [ i for i in self.filelist1.files if i not in self.filelist2.files ]
        list2 = [ i for i in self.filelist2.files if i not in self.filelist1.files ]
        message = f'''Portfolio '{self.portfolio}' mismatch
{self.folder1} : {list1}
{self.folder2} : {list2}
'''
        return message

class InvalidFilenameException( Exception ):
    '''Raised when the regular expression matching fails to recognize the filename'''
    def __init__( self, filename ):
        self.filename = filename

    def __str__( self ):
        return f'Invalid filename {self.filename}'

class CommandLineArgument:
    '''Process the command line arguments'''
    def __init__( self ):
        '''Constructor'''
        self.dry_run = None
        self.keep_source = None
        self.folder_list = None
        self.process_command_line_argument()

    def process_command_line_argument( self ):
        '''Process the command line argument'''
        parser = argparse.ArgumentParser()
        parser.add_argument( "folders", nargs="*" )
        parser.add_argument( "-d", "--dry-run", action="store_true",
                             help="Just print sources and destinations but do not really copy" )
        parser.add_argument( "-m", "--keep-source", action="store_true",
                             help="Keep the source folder intact" )
        args = parser.parse_args()

        self.dry_run = args.dry_run
        self.keep_source = args.keep_source
        self.folder_list = args.folders

    def __str__( self ):
        return f'dryRun: {self.dry_run}, keepSource: {self.keep_source},' + \
                f' sources: {self.folder_list}'

class CopyInfo:
    '''Command to copy the source file to the destination file'''
    def __init__( self, src, dst ):
        self.src = src
        self.dst = dst

    def __str__( self ):
        return f'{self.src} ---> {self.dst}'

class FileList:
    '''A list of all files, excluding extension, in a folder.
    We will use this to compare if two folders contain the same file or not.
    '''
    def __init__( self, folder, keep_extension=False ):
        self.folder = folder
        self.files = self.list_file( keep_extension )

    def list_file( self, keep_extension=False ):
        '''List and return all files in the directory'''
        check_if_folder_exists( self.folder )
        content = [ name for name in os.listdir( self.folder )
                    if name[ 0 ] != '.' and
                    os.path.isfile( os.path.join( self.folder, name ) ) ]
        if not keep_extension:
            content = [ os.path.splitext( f )[ 0 ] for f in content ]
        return sorted( content )

    def __eq__( self, other ):
        if len( self.files ) != len( other.files ):
            return False
        return self.files == other.files

    def __str__( self ):
        all_files = ', '.join( self.files )
        return f'{self.folder} : [ {all_files} ]'

def check_portfolio_sanity( config ):
    '''Do sanity check before we do the actual works
    1) Check if all destination folders exist
    2) Check if all folders in each portfolio have the same content
    '''
    for destination in config[ "Destinations" ].values():
        check_if_folder_exists( destination )

    portfolio = config[ "Portfolio" ]
    portfolio_location = config[ "Destinations" ][ "Portfolio" ]

    for name, info in portfolio.items():
        port_folders = info[ 'Destinations' ][ 'Portfolio' ]

        file_list_obj = []
        for folder in port_folders:
            abs_path = os.path.join( portfolio_location, name, folder )
            check_if_folder_exists( abs_path )
            file_list_obj.append( ( folder, FileList( abs_path ) ) )

        for i in range( len( file_list_obj ) - 1 ):
            folder1, filelist1  = file_list_obj[ i ]
            folder2, filelist2  = file_list_obj[ i + 1 ]
            if filelist1 != filelist2:
                raise PortfolioMismatchException( name, folder1, filelist1,
                                                  folder2, filelist2 )

def get_next_index( config ):
    '''Return the next index for each folder in the portfolio'''
    portfolio = config[ "Portfolio" ]
    portfolio_location = config[ "Destinations" ][ "Portfolio" ]

    next_index = {}
    for name, info in portfolio.items():
        if not info.get( "baseName", None ):
            # This portfolio does not need renaming
            continue

        folder = info[ 'Destinations' ][ 'Portfolio' ][ 0 ]
        abs_path = os.path.join( portfolio_location, name, folder )
        file_list = FileList( abs_path ).files
        if file_list:
            last_file = file_list[ -1 ]
            search_obj = re.search( r'[a-zA-Z\s]+(\d+)', last_file )
            if not search_obj:
                raise InvalidFilenameException( last_file )
            next_index[ name ] = int( search_obj.group( 1 ) ) + 1
        else:
            next_index[ name ] = 1
    return next_index

class Portfolio:
    '''A protforlio object represents each folder in the porfolio e.g. Abstract, Astrophotograhy'''
    def __init__( self, folder, config ):
        self.folder = folder
        self.config = config

    def get_key_words( self, filename ):
        '''Get the keywords from the image file'''
        image = Image.open( filename )
        image.verify()
        if image.format != 'JPEG':
            return None

        try:
            iptc = iptcinfo3.IPTCInfo( filename )
            image_tags = iptc[ 'keywords' ]
            if image_tags:
                if isinstance( image_tags, list ):
                    image_tags = [ i.decode() if isinstance( i, bytes ) else i for i in image_tags ]
                elif isinstance( image_tags, bytes ):
                    image_tags = image_tags.decode()
                return image_tags
        except Exception as exception:
            if str( exception ) != "No IPTC data found.":
                raise

        return None

    def process( self, next_index ):
        subfolders = self.config[ "SourceSubfolders" ]
        tagged_subfolder = self.config[ "TaggedSubfolder" ]
        location_dict = self.config[ "Destinations" ]

        # Create the mappign from a keyword to a list of Path
        subfolder_path = os.path.join( self.folder, tagged_subfolder )
        check_if_folder_exists( subfolder_path )
        path_obj = Path( subfolder_path )
        all_files = list( path_obj.iterdir() )
        # Skip hidden files which start with '.'
        all_files = [ f for f in all_files if f.name[ 0 ] != '.' ]
        keyword_dict = defaultdict( list )
        for image in all_files:
            keywords = self.get_key_words( image )
            if not keywords:
                continue
            keyword = keywords[ 0 ]
            keyword_dict[ keyword ].append( image.name )

        # Expand the keyword_dict to the following format
        # {'Abstract': [{'Full': 'Abstract/Full/Abstract 001.jpg',
        #                'PSD': 'Abstract/PSD/Abstract 001.psd/psb',
        #                'Web': 'Abstract/Web/Abstract 001.jpg'},
        #              ]
        # }
        keyword_src_dict = defaultdict( list )
        for keyword, filelist in keyword_dict.items():
            source_folders = self.config[ "SourceSubfolders" ]
            for filename in filelist:
                src_dir = {}
                for port_folder in source_folders:
                    basename, _ = os.path.splitext( filename )
                    src_filename = None
                    extensions = [ '.jpg', '.psd', '.psb' ]
                    for ext in extensions:
                        candidate = os.path.join( self.folder, port_folder, f'{basename}{ext}' )
                        if os.path.exists( candidate ):
                            src_filename = candidate
                    if src_filename:
                        src_dir[ port_folder ] = src_filename
                keyword_src_dict[ keyword ].append( src_dir )

        def get_dst_filename( src, basename=None, index=None ):
            '''Get the destination filename from the source filename'''
            if basename is not None and index is not None:
                _, ext = os.path.splitext( src )
                return f'{basename} {index:04d}{ext}'
            return src

        commands = []
        for keyword, src_files in keyword_src_dict.items():
            for src_file in src_files:
                index = None
                basename = self.config[ "Portfolio" ][ keyword ].get( "baseName", None )
                if basename:
                    index = next_index[ keyword ]
                    next_index[ keyword ] += 1

                for destination, locations in \
                        self.config[ "Portfolio" ][ keyword ][ "Destinations" ].items():
                    if isinstance ( locations, list ):
                        for location in locations:
                            src = src_file.get( location, None )
                            if not src:
                                raise SourceFileNotFound( location, src_file )
                            dst_filename = get_dst_filename( src, basename, index )
                            dst = os.path.join( location_dict[ destination ], keyword,
                                                location, dst_filename )
                            commands.append( CopyInfo( src, dst ) )
                    else:
                        src = src_file[ locations ]
                        dst_filename = get_dst_filename( src, basename, index )
                        dst = os.path.join( location_dict[ destination ], keyword, dst_filename )
                        commands.append( CopyInfo( src, dst ) )

        return commands

def process_copy_command( commands, dry_run ):
    '''Execute all copy commands'''
    size = len( commands )
    for count, command in enumerate( commands ):
        print( f'{count + 1}/{size} {command}', flush=True )
        if not dry_run:
            shutil.copy( command.src, command.dst )

def move_source_folders( config, folder_list ):
    '''Move the source folders to the processed location'''
    processed_location = config[ "ProcessedLocation" ]
    for src in folder_list:
        obj = re.match( r'(\d{4})-\d{2}-\d{2} .*', src )
        if not obj:
            print( f'Unable to move {src} to {processed_location}' )
            continue

        year = obj.group( 1 )
        dst = os.path.join( processed_location, year )
        shutil.move( src, dst )

def main():
    '''Main program'''
    arguments = CommandLineArgument()

    try:
        config = load_config( CONFIG_FILE )
        check_portfolio_sanity( config )
        next_index = get_next_index( config )

        # Generate the list of copy commands
        commands = []
        for source in arguments.folder_list:
            print( f'processing {source}' )
            portfolio = Portfolio( source, config )
            commands += portfolio.process( next_index )

        process_copy_command( commands, arguments.dry_run )
        if not arguments.dry_run and not arguments.keep_source:
            move_source_folders( config, arguments.folder_list )
    except ( FileNotFound,
             DirectoryNotFound,
             PortfolioMismatchException,
             InvalidFilenameException ) as error:
        print( 'Program abnormally terminated')
        print( error )
        sys.exit( 1 )
    except Exception as error:
        print( 'Program abnormally terminated')
        print( error )
        raise

if __name__ == '__main__':
    main()

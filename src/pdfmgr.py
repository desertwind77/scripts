#!/usr/bin/env python3
'''
A script to manage PDF files
'''

from typing import List
import argparse
import random
import sys
# pylint: disable=import-error
import PyPDF2


def open_pdf(filename: str) -> PyPDF2._reader.PdfReader:
    '''Open a PDF file for reading

    Args:
        filename (str): the source PDF filename
    '''
    reader = None
    try:
        reader = PyPDF2.PdfReader(filename)
    except FileNotFoundError:
        print(f'{filename} not found', file=sys.stderr)
        sys.exit(1)
    return reader


def write_pdf(filename: str, writer: PyPDF2._writer.PdfWriter) -> None:
    '''Write the content of the writer to filename

    Args:
        filename (str): the destination PDF filename
    '''
    try:
        with open(filename, "wb") as file:
            writer.write(file)
    except OSError:
        print(f'Unable to write to {filename}', file=sys.stderr)
        sys.exit(1)


def encrypt(src: str, dst: str, password: str) -> None:
    '''
    Encrypt the source file (src) with the password
    and save to the new file (dst)

    Args:
        src (str): the source PDF file

        dst (str): the destination PDF file
    '''
    reader = open_pdf(src)
    writer = PyPDF2.PdfWriter()

    # Add all pages from the original file
    for page in reader.pages:
        writer.add_page(page)

    # Encrypt the new file with the password
    writer.encrypt(password)
    write_pdf(dst, writer)


def decrypt(src: str, dst: str, password: str) -> None:
    '''
    Decrypt the source file (src) with the password
    and save to the new file (dst)

    Args:
        src (str): the source PDF file

        dst (str): the destination PDF file
    '''
    reader = open_pdf(src)
    writer = PyPDF2.PdfWriter()

    if reader.is_encrypted:
        reader.decrypt(password)

    # Add all pages from the original file
    for page in reader.pages:
        writer.add_page(page)

    write_pdf(dst, writer)


def reverse(src: str, dst: str) -> None:
    '''Reverse the page order in a PDF file

    Args:
        src (str): the source PDF file

        dst (str): the destination PDF file
    '''
    reader = open_pdf(src)
    writer = PyPDF2.PdfWriter()

    for page in reader.pages:
        # Insert the page at the first position
        writer.insert_page(page, index=0)

    write_pdf(dst, writer)


def interleave(odd: str, even: str, dst: str) -> None:
    '''Interleave two pdf files, one of which contains only the odd pages and
    the other contains only the even pages, and then save to the destination
    PDF file

    Args:
        odd (str): the source file containing the odd pages

        even (str): the source file containing the even pages

        dst (str): the destination PDF file
    '''
    odd_reader = open_pdf(odd)
    even_reader = open_pdf(even)
    writer = PyPDF2.PdfWriter()

    odd_len = len(odd_reader.pages)
    even_len = len(even_reader.pages)
    if (odd_len < even_len) or (odd_len - even_len > 1):
        print('Page number check failed.', file=sys.stderr)
        print(f'   {odd} has {odd_len} pages', file=sys.stderr)
        print(f'   {even} has {even_len} pages', file=sys.stderr)
        sys.exit(1)

    page_tubles = zip(odd_reader.pages, even_reader.pages)
    for pages in page_tubles:
        writer.add_page(pages[0])
        writer.add_page(pages[1])

    if odd_len - even_len == 1:
        writer.add_page(odd_reader.pages[odd_len - 1])

    write_pdf(dst, writer)


def merge(sources: List[str], dst: str) -> None:
    '''Merge multiple PDF files into a single PDF file

    Args:
        sources (str): the list of the source PDF files to merge

        dst (str): the destination PDF file
    '''

    if len(sources) < 2:
        print('No file to merge', file=sys.stderr)
        sys.exit(1)

    try:
        merger = PyPDF2.PdfMerger()
        for pdf in sources:
            merger.append(pdf)

        merger.write(dst)
        merger.close()
    except PyPDF2.errors.FileNotDecryptedError:
        print('Unable to merge encrypted pdf files', file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


def parse(source: str, dst: str) -> None:
    '''Extract text from a PDF file and save to a text file

    Args:
        source (str): the source PDF file

        dst (str): the destination text file
    '''
    reader = PyPDF2.PdfReader(source)

    text = ''
    for page in reader.pages:
        text += page.extract_text()

    if not dst:
        print(text)
    else:
        with open(dst, 'w', encoding="utf8") as output:
            print(text, file=output)


def parse_arguments() -> argparse.Namespace:
    '''Parse the command line argument

    Args:
        None

    Return:
        argparse.Namespace: parsed command line arguments
    '''
    parser = argparse.ArgumentParser(description='PDF manager')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    encrypt_parser = subparsers.add_parser('encrypt',
                                           help='Encrypt a pdf file')
    encrypt_parser.add_argument('-s', '--src', required=True, action='store',
                                dest='src', help='Source file')
    encrypt_parser.add_argument('-d', '--dst', action='store', dest='dst',
                                help='Destination file')
    encrypt_parser.add_argument('-p', '--password', required=True,
                                action='store', dest='passwd', help='Password')

    decrypt_parser = subparsers.add_parser('decrypt',
                                           help='Decrypt a pdf file')
    decrypt_parser.add_argument('-s', '--src', required=True, action='store',
                                dest='src', help='Source file')
    decrypt_parser.add_argument('-d', '--dst', action='store', dest='dst',
                                help='Destination file')
    decrypt_parser.add_argument('-p', '--password', required=True,
                                action='store', dest='passwd', help='Password')

    parse_parser = subparsers.add_parser('parse',
                                         help='Parse text from a pdf file')
    parse_parser.add_argument('-s', '--src', required=True, action='store',
                              dest='src', help='Source file')
    parse_parser.add_argument('-d', '--dst', action='store', dest='dst',
                              help='Destination file')

    reverse_parser = subparsers.add_parser('reverse',
                                           help='Reverse a pdf file')
    reverse_parser.add_argument('-s', '--src', action='store', required=True,
                                dest='src', help='Source file')
    reverse_parser.add_argument('-d', '--dst', action='store', dest='dst',
                                help='Destination file')

    help_message = 'Interleave two pdf files which one containing' + \
                   ' odd pages and the other even pages'
    interleave_parser = subparsers.add_parser('interleave', help=help_message)
    help_message = 'Source file containing the odd page' + \
                   ' (assuming the pdf page starting from page 1)'
    interleave_parser.add_argument('-o', '--odd', action='store',
                                   required=True, dest='odd',
                                   help=help_message)
    interleave_parser.add_argument('-e', '--even', action='store',
                                   required=True, dest='even',
                                   help='Source file containing the even page')
    interleave_parser.add_argument('-d', '--dst', action='store', dest='dst',
                                   help='Destination file')

    merge_parser = subparsers.add_parser('merge', help='Merge pdf files')
    merge_parser.add_argument('sources', nargs='*')
    merge_parser.add_argument('-d', '--dst', action='store', dest='dst',
                              help='Destination file')
    return parser.parse_args()


def main() -> None:
    '''The main function'''
    args = parse_arguments()

    dst = args.dst
    if not dst and args.command != 'parse':
        rand_num = random.randrange(1000, 10000)
        dst = f'pdfmgr_output_{rand_num}.pdf'

    if args.command == 'encrypt':
        encrypt(args.src, dst, args.passwd)
    elif args.command == 'decrypt':
        decrypt(args.src, dst, args.passwd)
    elif args.command == 'parse':
        parse(args.src, dst)
    elif args.command == 'reverse':
        reverse(args.src, dst)
    elif args.command == 'interleave':
        interleave(args.odd, args.even, dst)
    elif args.command == 'merge':
        merge(args.sources, dst)

    if not args.dst:
        print(f'Saved the output to {dst}')


if __name__ == '__main__':
    main()

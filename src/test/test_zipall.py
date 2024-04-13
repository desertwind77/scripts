#!/usr/bin/env python3
'''Test file for the zipall.py script'''

# pylint: disable=redefined-outer-name
# pylint: disable=import-error
from pathlib import Path
import os
import tempfile
import pytest
from zipall import zip_folder


def create_file(filename: str) -> None:
    '''Create a new temp file for our testing

    Args:
        filename (str): the name of the file

    Returns:
        None
    '''
    with open(filename, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write(f'This is {filename}')


def get_folder_content(folder: str) -> list[str]:
    '''Get the list of files and subfolders in the folder

    Args:
        folder (str): the name of the folder

    Returns:
        list[str]: the list of files and subfolders
    '''
    return sorted(os.listdir(folder))


@pytest.fixture()
def folders():
    '''Returns the folder names'''
    return ['folder1']


@pytest.fixture()
def hidden_files():
    '''Returns the hidden files'''
    return ['.hidden_file.txt']


@pytest.fixture()
def non_hidden_files():
    '''Returns the non-hidden files'''
    return ['file1.txt', 'file2.txt', 'file3.txt']


@pytest.fixture()
def original_files(non_hidden_files, hidden_files, folders):
    '''Returns both the hidden and non-hidden files'''
    return sorted([*non_hidden_files, *hidden_files, *folders])


@pytest.fixture()
def zip_files(non_hidden_files):
    '''Return the expected zip files in the temp directory'''
    return sorted([Path(f).stem + '.zip' for f in non_hidden_files])


@pytest.fixture()
def tmp_dir_name(hidden_files, non_hidden_files, folders):
    '''This fixture creates a temporary directory and its original files.'''
    with tempfile.TemporaryDirectory() as dir_name:
        # Create a temp folder and some files in it
        for filename in [*hidden_files, *non_hidden_files]:
            filename = os.path.join(dir_name, filename)
            create_file(filename)

        for folder in folders:
            os.mkdir(os.path.join(dir_name, folder))

        # If we return here, the context manager will clean up tmp_dir_name.
        # So we yield, instead of return, here.
        yield dir_name


def test_dry_run(tmp_dir_name, original_files):
    '''Verify the dry run mode'''
    zip_folder(tmp_dir_name, dry_run=True)
    assert original_files == get_folder_content(tmp_dir_name)


@pytest.mark.zip
def test_zip(tmp_dir_name, original_files, zip_files):
    '''Verify the zip functionality'''
    zip_folder(tmp_dir_name)
    expected = sorted([*original_files, *zip_files])
    assert expected == get_folder_content(tmp_dir_name)


@pytest.mark.zip
@pytest.mark.delete
def test_zip_delete(tmp_dir_name, hidden_files, folders, zip_files):
    '''Verify the zip functionality with the delete option'''
    zip_folder(tmp_dir_name, delete=True)
    expected = sorted([*hidden_files, *folders, *zip_files])
    assert expected == get_folder_content(tmp_dir_name)


@pytest.mark.unzip
def test_unzip(tmp_dir_name, original_files, hidden_files,
               folders, zip_files):
    '''Verify the unzip functionality'''
    # Prepare the temp folder for further testing
    zip_folder(tmp_dir_name, delete=True)
    expected = sorted([*hidden_files, *folders, *zip_files])
    assert expected == get_folder_content(tmp_dir_name)

    # Verify unzip
    zip_folder(tmp_dir_name, unzip=True)
    expected = sorted([*original_files, *zip_files])
    assert expected == get_folder_content(tmp_dir_name)


@pytest.mark.unzip
@pytest.mark.delete
def test_unzip_delete(tmp_dir_name, original_files, hidden_files,
                      folders, zip_files):
    '''Verify the unzip functionality with the delete option'''
    # Prepare the temp folder for further testing
    zip_folder(tmp_dir_name, delete=True)
    expected = sorted([*hidden_files, *folders, *zip_files])
    assert expected == get_folder_content(tmp_dir_name)

    # Verify unzip with delete
    zip_folder(tmp_dir_name, unzip=True, delete=True)
    assert original_files == get_folder_content(tmp_dir_name)

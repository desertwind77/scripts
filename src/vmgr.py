#!/usr/bin/env python3
'''
vmgr : intsall, update, or uninstall vim plugins
'''
from pathlib import Path
import argparse
import logging
import os
import shutil
import sys

from tabulate import tabulate
from utils import ConfigFileBase, check_exists, execute, setup_logging


class PluginConfig(ConfigFileBase):
    '''Information about vim plugins from the config'''
    def __init__(self, filename: str) -> None:
        '''Constructor

        Args:
            filename (str): the JSON configuration file
        '''
        super().__init__(filename)
        self.plugins = self.config['Plugins']
        self.vim_dir = self.config['InstallInfo']['VimDir']
        self.plugin_dir = self.config['InstallInfo']['PluginDir']
        self.git_repo = self.config['InstallInfo']['GitRepo']

class ViPluginManager:
    '''Vi plugin manger'''
    def __init__(self, filename: str) -> None:
        '''Constructor

        Args:
            filename (str): the JSON configuration file
        '''
        self.pinfo = PluginConfig(filename)

    def show(self) -> None:
        '''Show all the plugins in the configuration file'''
        tab_header = ['Plugin', 'Enable', 'Description']
        tab_width = [None, 6, 80]
        tab_data = []
        for name, data in self.pinfo.plugins.items():
            desc = data['Desc']
            enable = data['Enable'] == 'True'
            tab_data.append([name, enable, desc])

        print(tabulate(tab_data, headers=tab_header, tablefmt="rounded_grid",
                       maxcolwidths=tab_width))

    def install(self, force: bool = False) -> None:
        '''Install all the plugins

        Args:
            force (bool): remove all existing plugins before installing new ones
        '''
        # Check if the plugin directory exists or not. If it does not exist, create
        # a new one. In case that the user specifies the force opttion, remove all
        # the old plugins.
        full_plugin_dir = os.path.join(self.pinfo.vim_dir, self.pinfo.plugin_dir)
        if not os.path.isdir(full_plugin_dir) or force:
            if force:
                shutil.rmtree(self.pinfo.vim_dir)
            # os.makedirs() create a directory recursively while os.mkdir()
            # does not do recursively
            os.makedirs(full_plugin_dir)

        # Save the current directory so that we can come back here later.
        # Then go into the .vim directory
        current_dir = os.getcwd()
        os.chdir(self.pinfo.vim_dir)

        # Initalize git repository if none exists
        if not os.path.isdir(self.pinfo.git_repo):
            cmd = ['git', 'init']
            if not execute(cmd):
                logging.error('unable to initialize the git repository')
                return

        # Install each plugins specified in the configuration file
        for name, data in self.pinfo.plugins.items():
            url = data['URL']
            enable = data['Enable'] == 'True'
            des = os.path.join(self.pinfo.plugin_dir, name)

            if not enable or os.path.isdir(des):
                # Skip the plugin if it is disabled or is already installed
                logging.info('Skipped %s', name)
                continue

            cmd = ['git', 'submodule', 'add', url, des]
            if not execute(cmd):
                logging.info('Failed %s', name)
                continue
            logging.info('Installed %s', name)

        # Commit the change
        cmd = ['git', 'commit', '-m', 'Vim plugin installation']
        execute(cmd)

        # Restore the initial current working directory
        os.chdir(current_dir)

    def uninstall(self, name: str) -> None:
        '''Uninstall a specific plugin

        Args:
            name (str): the plugin to be uninstalled
        '''
        check_exists(self.pinfo.vim_dir, is_file=False)
        check_exists(os.path.join(self.pinfo.vim_dir, self.pinfo.plugin_dir, name),
                     is_file=False)

        # Save the current directory so that we can come back here later.
        # Then go into the .vim directory
        current_dir = os.getcwd()
        os.chdir(self.pinfo.vim_dir)
        des = os.path.join(self.pinfo.plugin_dir, name)

        cmds = [
            ['git', 'submodule', 'deinit', '--force', des],
            ['git', 'rm', des],
            ['git', 'commit', '-m', f'Removing {name}'],
        ]

        for cmd in cmds:
            if not execute(cmd):
                logging.error('unable to uninstall %s', name)
                os.chdir(current_dir)
                return

        git_dest = os.path.join(self.pinfo.git_repo, 'modules', des)
        shutil.rmtree(git_dest)

        # Commit the change
        cmd = ['git', 'commit', '-a', '-m', f'Uninstall {name}']
        execute(cmd, discard_error=True)

        # Restore the initial current working directory
        os.chdir(current_dir)

        logging.info('Uninstalled %s', name)

    def update(self) -> None:
        '''Update all the plugins'''
        check_exists(self.pinfo.vim_dir, is_file=False)

        # Save the current directory so that we can come back here later.
        # Then go into the .vim directory
        current_dir = os.getcwd()
        os.chdir(self.pinfo.vim_dir)

        # We can run either of the following commands
        #     git submodule update --remote --merge
        #     git submodule update --init --recursive
        cmd = ['git', 'submodule', 'update', '--remote', '--merge']
        if not execute(cmd):
            logging.error('unable to update plugins')
            os.chdir(current_dir)
            return

        # Commit the change and ignore the error because git commit may
        # return a non-zero code when there is nothing to commit.
        cmd = ['git', 'commit', '-a', '-m', 'Update plugins']
        execute(cmd, discard_error=True)

        # Restore the initial current working directory
        os.chdir(current_dir)

        logging.info('Updated all plugins')


def parse_argv() -> argparse.Namespace:
    '''Parse the command line arguments

    Returns:
        (argparse.Namespace) parsed command line arguments
    '''
    parser = argparse.ArgumentParser(description='vi plugin manager')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Print log message')
    parser.add_argument('config', action='store', help='configuraiton file')

    subparser = parser.add_subparsers(dest='command')
    subparser.required = True

    subparser.add_parser('show', help='show all vim plugins to be installed')

    install_parser = subparser.add_parser('install', help='install all vim plugins')
    install_parser.add_argument('-f', '--force', action='store_true', dest='force')

    subparser.add_parser('update', help='update all vim plugins')

    uninstall_parser = subparser.add_parser('uninstall', help='uninstall a plugin')
    uninstall_parser.add_argument('name', action='store', help='plugin name')

    return parser.parse_args()


def main():
    '''The main functions'''

    # Make sure that the script is not run inside .vim directory.
    # This script will create a new .vim directory.
    if '.vim' in str(Path('.').absolute()):
        print('This command must run outsite the .vim folder.')
        sys.exit(1)

    args = parse_argv()
    setup_logging(verbose=True)

    manager = ViPluginManager(args.config)
    if args.command == 'install':
        manager.install(args.force)
    elif args.command == 'uninstall':
        manager.uninstall(args.name)
    elif args.command == 'update':
        manager.update()
    elif args.command == 'show':
        manager.show()


if __name__ == '__main__':
    main()

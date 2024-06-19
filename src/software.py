#!/usr/bin/env python3
'''
Install packages on different OSs
'''

import argparse

from utils import load_config

CONFIG_FILENAME='config/software.json'


def process_arguments():
    '''Process commandline arguments'''
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='platform', choices=['linux', 'mac', 'pi', 'all'])
    return parser.parse_args()


def generate_commands(config):
    '''Generate the commands for the platfrom'''
    if 'pre-install' in config:
        for cmd in config["pre-install"]:
            print(cmd)
        print()

    if 'packages' in config:
        packages_config = config['packages']
        for group, packages in packages_config['groups'].items():
            print(f'# Installing {group}')
            cmd = packages_config['command']
            cmd = cmd + ' ' + ' '.join(packages)
            print(cmd)
            print()

    if 'custom' in config:
        for group, info in config['custom'].items():
            print(f'# Installing {group}')
            for cmd in info['commands']:
                print(cmd)
            print()


def main():
    '''The main function'''
    config = load_config(__file__, CONFIG_FILENAME)
    args = process_arguments()
    platform_config = config['Platforms'][args.platform]
    generate_commands(platform_config)


if __name__ == '__main__':
    main()

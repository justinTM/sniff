from argparse import ArgumentParser
import os
import configparser
import sys
from typing import Any


DEFAULT_CONFIG_FILE = os.path.join(os.getcwd(), "config.ini")


# Function to convert string to boolean
def str2bool(v):
    if not isinstance(v, str):
        return v
    elif v.lower() in ('yes', 'true', 't', 'y'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n'):
        return False
    else:
        return v


def get_or_write_config(parser: ArgumentParser, filepath: str = None):
    args: dict[str, Any] = vars(parser.parse_args(sys.argv[1:]))
    filepath = filepath or args.pop("config_file", DEFAULT_CONFIG_FILE)

    # check for config file and load or generate it
    config = configparser.ConfigParser()
    if os.path.exists(filepath):
        # load the config file
        config.read(filepath)
        if 'DEFAULT' in config:
            # override default argparse values with config values
            defaults = {k: str2bool(v) for k, v in config['DEFAULT'].items()}
            parser.set_defaults(**defaults)
    else:
        # generate the config file with default argparse values
        args = parser.parse_args()  # this will be the defaults initially
        config['DEFAULT'] = {k: str(getattr(args, k)) for k in vars(args)}
        defaults = {k: str2bool(v) for k, v in config['DEFAULT'].items()}
        parser.set_defaults(**defaults)
        with open(filepath, 'w') as configfile:
            config.write(configfile)

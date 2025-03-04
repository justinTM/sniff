import logging as log
import json
from typing import Any
from dpath import util

import sniff.params as ps


class DataSenderReader():
    """Parse and search Teltonika Data to Server config file"""
    DEFAULT_PATH = ps.DATA_SENDER_CONFIG_PATH  # eg. /etc/config/data_sender
    DEFAULT_HTTP_HOST_KEY = ps.DEFAULT_QUERY_API_URL  # eg. **/http_host

    def __init__(self, filepath=DEFAULT_PATH):
        err = None
        self.path = filepath
        self.config = None
        log.info(f"reading config file '{filepath}'...")
        try:
            open(filepath, 'r')
        except FileNotFoundError:
            err = f"no such Data To Server config file '{filepath}'"
        except IOError as e:
            err = f"couldn't read config file '{filepath}': {e}"

        if err:
            raise FileNotFoundError(err)

    def parse(self, path=None):
        """_summary_

        Args:
            filepath (_type_): _description_

        Returns:
            _type_: _description_

        Example:
            >>> from sniff.reader import DataSenderReader
            >>> dsr = DataSenderReader("/etc/config/data_to_server")
            >>> print(json.dumps(dsr.parse(), indent=4))
            {
                "settings settings": {
                    "__type__": "settings",
                    "__name__": "settings",
                    "loglevel": "1"
                },
                "collection 1": {
                    "__type__": "collection",
                    "__name__": "1",
                    "sender_id": "1",
                    "name": "aws_wifi",
                    "output": "2",
                    "retry_timeout": "1",
                    "period": "10",
                    "retry": "1",
                    "retry_count": "10",
                    "input": [
                        "3",
                        "4",
                        "5"
                    ],
                    "format": "json",
                    "enabled": "0"
                },
                "input 3": {
                    "__type__": "input",
                    "__name__": "3",
                    "plugin": "base",
                    "format": "json",
                    "name": "base"
                },
                "output 2": {
                    "__type__": "output",
                    "__name__": "2",
                    "name": "aws_wifi_output",
                    "plugin": "http",
                    "http_header": [
                        "content-type: text/plain; charset=utf-8"
                    ],
                    "http_host": "https://nfo0uh35ye.execute-api.us-east-2.amazonaws.com/",
                    "http_tls": "0"
                },
                "input 4": {
                    "__type__": "input",
                    "__name__": "4",
                    "format": "json",
                    "wifi_segments": "64",
                    "wifi_filter": "all",
                    "plugin": "wifiscan",
                    "name": "wifi"
                },
                "input 5": {
                    "__type__": "input",
                    "__name__": "5",
                    "format": "json",
                    "plugin": "mnfinfo",
                    "name": "mnf"
                }
            }
        """  # noqa
        config_data: dict[str, Any] = {}
        current_block = None
        filepath = path or self.path

        log.info(f"parsing Data to Server config: {self.path}")
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('config'):
                    parts = line.split()
                    # Handles cases like "config settings 'settings'"
                    block_type, block_name = parts[1], parts[2].strip("'")
                    current_block = f"{block_type} {block_name}"
                    config_data[current_block] = {
                        '__type__': block_type, '__name__': block_name}
                elif line.startswith('option'):
                    if current_block is not None:
                        parts = line.split()
                        option_key = parts[1]
                        option_value = ' '.join(parts[2:]).strip("'")
                        config_data[current_block][option_key] = option_value
                elif line.startswith('list'):
                    if current_block is not None:
                        parts = line.split()
                        list_key = parts[1]
                        list_value = ' '.join(parts[2:]).strip("'")
                        if list_key not in config_data[current_block]:
                            config_data[current_block][list_key] = []
                        config_data[current_block][list_key].append(list_value)

        log.debug(f"got config file:\n{json.dumps(config_data, indent=4)}")
        log.info("done.")
        self.config = config_data

        return config_data

    def search(self, dpath_query=DEFAULT_HTTP_HOST_KEY):
        """Search the Teltonika Data to Server for a specific key

        Args:
            dpath_query (_type_, optional): _description_. Defaults to DEFAULT_HTTP_HOST_KEY.

        Returns:
            _type_: _description_

        Example:
            >>> from sniff.reader import DataSenderReader
            >>> dsr = DataSenderReader("/etc/config/data_to_server")
            >>> dsr.parse()["output 2"]["http_host"]
            'https://nfo0uh35ye.execute-api.us-east-2.amazonaws.com/'
            >>> dsr.search("**/http_host")
            'https://nfo0uh35ye.execute-api.us-east-2.amazonaws.com/'

        """  # noqa
        value = ""
        query = dpath_query
        log.debug(f"searching '{self.path}' for key '{query}'...")
        if not self.config:
            self.parse()
        try:
            values = list(util.search(self.config, query, yielded=True))
            if len(values) > 1:
                log.warning(f"{len(values)}>1 occurences of {query}: {values}")
            for path, value in values:
                log.debug(f"Found {query}='{value}' at {path}")
            return value
        except KeyError:
            log.error(f"KeyError: couldn't find {query} in {self.path}")
        except FileNotFoundError:
            log.error(f"FileNotFound: couldn't find {query} in {self.path}")

        return value

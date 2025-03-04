import os
# from ubus import reader
# from typing import Any


def make_file(file: str, dir="/var/log", dir_backup="/tmp/log"):
    """try default logging location or create one if not exists."""
    try:
        path = os.path.join(dir, file)
        open(path, "w").close()
        return path
    except PermissionError:
        path = make_file(file, dir=dir_backup)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path


LOG_PATH = make_file(f"{__package__}.log")
LOG_LEVEL = "INFO"

PATH_ETC_CONFIG_SYSTEM = "/etc/config/system"

IS_LOG_TO_CONSOLE = False

LOG_FORMAT = r"%(asctime)s %(levelname)s - %(message)s [%(funcName)s() %(filename)s:%(lineno)d]"  # noqa
LOG_FILE_SPLIT_WHEN = "midnight"
LOG_FILE_SUFFIX = "%Y-%m-%d"

# DATA_SENDER_CONFIG = reader.parse_config_file(DATA_SENDER_CONFIG_PATH)
# DATA_SENDER: dict[str, Any] = DATA_SENDER_CONFIG.get("output 2", {})

DATA_SENDER_CONFIG_PATH = "/etc/config/data_sender"
DEFAULT_API_HEADERS = "content-type: text/plain; charset=utf-8"
DEFAULT_QUERY_API_URL = "**/http_host"
DEFAULT_QUERY_API_HEADERS = "**/http_header"
API_URL = os.environ.get("BLE_API_URL")
API_HEADER = os.environ.get("BLE_API_HEADER")
# data_header = DATA_SENDER.get("http_header")
# data_header = {data_header.split(": ")[0]: data_header.split(": ")[1]}
API_HEADER = API_HEADER or DEFAULT_API_HEADERS

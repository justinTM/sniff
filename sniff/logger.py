import logging
import sys
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

import sniff.params as ps

LEVELS = ", ".join([k for k in logging._nameToLevel.keys()])


def init_logger(log_path=ps.LOG_PATH,
                log_level=ps.LOG_LEVEL,
                log_format=ps.LOG_FORMAT,
                is_log_to_console=ps.IS_LOG_TO_CONSOLE,
                **kwargs):

    level = logging._nameToLevel.get(log_level)
    format = logging.Formatter(log_format)

    log = logging.getLogger()
    _ = [log.removeHandler(h) for h in log.handlers]
    log.setLevel(logging.DEBUG)

    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when=ps.LOG_FILE_SPLIT_WHEN,
        backupCount=30)
    file_handler.suffix = ps.LOG_FILE_SUFFIX
    file_handler.setLevel(level)
    file_handler.setFormatter(format)
    log.addHandler(file_handler)

    # log only errors to console, unless enabled or log level is debug
    console_handler = StreamHandler(sys.stderr)
    if is_log_to_console or level == logging.DEBUG:
        console_handler.setLevel(level)
    else:
        console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(format)
    log.addHandler(console_handler)

    log.debug(f"""set logging properties:
    log_path={log_path}
    log_level={log_level}
    log_format={log_format}
    is_log_to_console={is_log_to_console}""")

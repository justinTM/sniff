from urllib.request import urlopen, Request
from urllib.error import HTTPError
import logging as log
import json
from typing import Any, MutableMapping, Union

from sniff import params as ps
from sniff.ubus import Ubus


def get_timezone(path_etc_config_system=ps.PATH_ETC_CONFIG_SYSTEM):
    c = f"cat {path_etc_config_system}"
    try:
        return Ubus.run_cmd(c).stdout.split("timezone '")[1].split("'")[0]
    except Exception:
        try:
            return Ubus.run_cmd("date +%Z%z").stdout.strip()
        except Exception:
            log.error(f"couldn't get timezone from '{c}' or 'date +%Z%z'!")
            return ""


def post_data(data: Union[dict[str, Any], list[Any]],
              url: str,
              headers: MutableMapping[str, str]):
    httprequest = Request(
        url=url,
        headers=headers,
        data=json.dumps(data).encode(),
        method="POST")

    try:
        with urlopen(httprequest) as response:
            log.debug(f"API response status: {response.status}")
            result = response.read().decode()
            log.debug(f"API response: {result}")
            return None, result
    except HTTPError as e:
        log.error(f"ERROR: {e}")
        return e, None

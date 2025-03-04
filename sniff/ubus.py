import subprocess
import json
from typing import Any, Callable
import time
import logging as log
import shlex
from abc import ABC

import sniff.parser

_PRIMS = (bool, str, int, float, type(None))
_NO_UBUS_EXC = "'['which', 'ubus']' returned non-zero exit status 1"
_REPLACE_EXC = " 'ubus' is not installed here. are you in OpenWRT?"


class Ubus(ABC):
    DEFAULT_RESULT_CMD = "which ubus"
    DEFAULT_SCAN_PARSER = sniff.parser.default_scan_parser

    def __init__(self,
                 result_cmd=DEFAULT_RESULT_CMD,
                 scan_parser=DEFAULT_SCAN_PARSER,
                 device_parser: Callable = None,
                 **kwargs):
        self.name = type(self).__name__
        self.result_cmd = result_cmd
        self.scan_parser = scan_parser
        self.device_parser = device_parser
        self.result: dict[str, Any] = {}
        self.start_s = 0
        self.end_s = 0
        self.elapsed_s = 0
        self.__debug_self__()

    def __debug_self__(self):
        log.debug(f"init'ing {type(self).__name__} with properties:")
        _td = {k: v for k, v in vars(self).items() if isinstance(v, _PRIMS)}
        log.debug(json.dumps(_td, indent=4))

    @staticmethod
    def run_cmd(cmd_str: str):
        log.debug(f"running command '{cmd_str}'...")
        r = subprocess.run(shlex.split(cmd_str),
                           check=True,
                           text=True,
                           capture_output=True)
        log.debug("command success.")
        return r

    @staticmethod
    def read_stdout(result: subprocess.CompletedProcess[str]):
        log.debug("decoding stdout from command...")
        try:
            obj = json.loads(result.stdout)
            log.debug(f"got results:\n{json.dumps(obj, indent=4)}")
        except json.decoder.JSONDecodeError as e:
            log.debug(f"stdout is not JSON: {e}")
            obj = result.stdout
        log.debug("done.")
        return obj

    def _get_results(self):
        self.start_s = self.start_s or time.time()
        results = Ubus.run_cmd(self.result_cmd)
        self.end_s = time.time()
        self.elapsed_s = self.end_s - self.start_s
        self.result = Ubus.read_stdout(results)
        self.start_s = 0  # reset after running
        return self.result

    def results(self):
        try:
            r = self._get_results()
            log.info(f"got {self.name} scan results after \
                      {round(self.elapsed_s, 1)}s.")
            return r
        except subprocess.CalledProcessError as e:
            log.error(e)
            return {}

    def filtered(self,
                 data: Any,
                 scan_parser: Callable = None,
                 device_parser: Callable = None):
        scan_parser = scan_parser or self.scan_parser
        device_parser = device_parser or self.device_parser

        return scan_parser(data, device_parser=device_parser)


class UbusWifi(Ubus):
    RESULT_CMD = """ubus call iwinfo scan '{"device": "wlan1"}'"""
    DEFAULT_SCAN_PARSER = sniff.parser.wifi_scan_parser
    DEFAULT_DEVICE_PARSER = sniff.parser.wifi_device_parser

    def __init__(self,
                 result_cmd=RESULT_CMD,
                 scan_parser=DEFAULT_SCAN_PARSER,
                 device_parser=DEFAULT_DEVICE_PARSER,
                 **kwargs):
        super().__init__(result_cmd, scan_parser, device_parser, **kwargs)


class UbusBLE(Ubus):
    DEFAULT_BLE_WAIT_S = 10  # seconds to wait after scanning

    SCAN_CMD = "ubus call blesem scan.start"
    RESULT_CMD = "ubus call blesem scan.result"
    DEFAULT_SCAN_PARSER = sniff.parser.ble_scan_parser
    DEFAULT_DEVICE_PARSER = sniff.parser.ble_device_parser

    def __init__(self,
                 result_cmd=RESULT_CMD,
                 scan_parser=DEFAULT_SCAN_PARSER,
                 device_parser=DEFAULT_DEVICE_PARSER,
                 wait_s=DEFAULT_BLE_WAIT_S,
                 scan_cmd=SCAN_CMD,
                 **kwargs):
        self.wait_s = wait_s
        self._scan_s = -1
        self.scan_cmd = scan_cmd
        super().__init__(result_cmd, scan_parser, device_parser, **kwargs)

    def scan(self):
        log.info("scanning...")
        self.start_s = time.time()
        try:
            _ = Ubus.run_cmd(self.scan_cmd)
        except subprocess.CalledProcessError as e:
            if "returned non-zero exit status 6" not in str(e):
                raise e
            log.warn("ble scan failed (too soon, wait before scanning)")
        self._scan_s = time.time()

    def results(self):
        if self._scan_s == -1:
            self.scan()
        log.debug(f"waiting up to {self.wait_s}s for BLE results...")
        while (time.time() - self._scan_s) < self.wait_s:
            time.sleep(0.25)
        self._scan_s = -1

        return super().results()


class UbusFW(Ubus):
    RESULT_CMD = "ubus call rut_fota get_info"

    def __init__(self, result_cmd=RESULT_CMD, **kwargs):
        super().__init__(result_cmd, **kwargs)

    def fw(self):
        return self.results().get("fw", "unknown")


class UbusSystem(Ubus):
    RESULT_CMD = "ubus call system board"

    def __init__(self, result_cmd=RESULT_CMD, **kwargs):
        super().__init__(result_cmd, **kwargs)

    def hostname(self):
        return self.results().get("hostname", "unknown")


class UbusMnf(Ubus):
    RESULT_CMD = "ubus call mnfinfo get"

    def __init__(self, result_cmd=RESULT_CMD, **kwargs):
        super().__init__(result_cmd, **kwargs)

    def mac_serial(self):
        r = self.results().get("mnfinfo", {})
        return {
            "serial": r.get("serial", "unknown"),
            "mac": r.get("mac", "unknown")}

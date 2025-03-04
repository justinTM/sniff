from typing import Any


def default_scan_parser(scan_results_obj: Any, **kwargs):
    return scan_results_obj


def wifi_device_parser(ubus_iwinfo_device_obj: dict[str, Any]):
    """Defines how to handle a single wifi device in a list of results from:
    ubus call iwinfo scan '{"device": "wlan1"}'
    """
    d = ubus_iwinfo_device_obj
    return {
        "quality": round(d.get("quality", 0)/d.get("quality_max", 70), 2),
        "rssi": d.get("signal", -99),
        "host": d.get("ssid", ""),
        "mac": d["bssid"],    # required, else Exception
    }


def ble_device_parser(ubus_ble_device_obj: dict[str, Any]):
    """Defines how to handle a single bluetooth device in a results list from:
   ubus call blesem scan.start
   ubus call blesem scan.result
    """
    d = ubus_ble_device_obj
    return {
        "rssi": d.get("rssi", -99),
        "host": d.get("name", ""),
        "mac": d["address"],  # required, else Exception
    }


def wifi_scan_parser(scan_result_obj: dict[str, list[dict[str, Any]]],
                     device_parser=wifi_device_parser):
    """Defines how to handle results of command:
    ubus call iwinfo scan '{"device": "wlan1"}'

    Example:
        >>> from sniff.parser import wifi_scan_parser
        >>> scan_result_obj = {
        ...     'results': [{'ssid': 'My Internet',
        ...         'bssid': '2:BD:89:F:A1:75',
        ...         'mode': 'Master',
        ...         'channel': 149,
        ...         'signal': -27,
        ...         'quality': 70,
        ...         'quality_max': 70,
        ...         'ht_operation': {'primary_channel': 9,
        ...             'secondary_channel_offset': 'unknown',
        ...             'channel_width': 20},
        ...         'vht_operation': {'channel_width': 40,
        ...             'center_freq_1': 80,
        ...             'center_freq_2': 2},
        ...         'encryption': {'enabled': True,
        ...             'wpa': [2],
        ...             'authentication': ['psk', 'sae', 'none'],
        ...             'ciphers': ['tkip', 'ccmp', 'gcmp', 'wrap', 'ckip']}}]}
        >>> wifi_scan_parser(scan_result_obj)

    """
    return [device_parser(d) for d in scan_result_obj.get("results", [])]


def ble_scan_parser(scan_result_obj: dict[str, list[dict[str, Any]]],
                    device_parser=ble_device_parser):
    """Defines how to handle results of command:
    ubus call blesem scan.result

    Example:
        >>> from sniff.parser import ble_scan_parser
        >>> scan_result_obj = {
        ...     'scanning': 1,
        ...         'devices': [
        ...             {'rssi': -61,
        ...              'address': '6C:FC:DE:B0:EE:16'},
        ...             {'name': 'Front Door',
        ...              'rssi': -74,
        ...              'address': 'F4:CE:36:AD:62:91'}]}
        >>> ble_scan_parser(scan_result_obj)
        [{'rssi': -61, 'host': '', 'mac': '6C:FC:DE:B0:EE:16'},
         {'rssi': -74, 'host': 'Front Door', 'mac': 'F4:CE:36:AD:62:91'}]
    """
    return [device_parser(d) for d in scan_result_obj.get("devices", [])]


def fw_scan_parser(scan_result_obj: dict[str, str], **kwargs):
    return {"fw": scan_result_obj.get("fw")}

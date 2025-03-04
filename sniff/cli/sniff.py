import argparse
import sys
import logging as log
import json
from subprocess import CalledProcessError

from sniff import sender, logger, reader, ubus
from sniff.ubus import UbusBLE, UbusWifi, UbusFW, UbusMnf, UbusSystem
import sniff.params as ps
from sniff.cli import config


def create_parser():
    parser = argparse.ArgumentParser(
        prog="sniff.py",
        description="a CLI tool to scan bluetooth and wifi \
            signals from `ubus` and send to AWS Lambda.")
    parser.add_argument(
        "--no-wifi",
        action='store_true',
        help="disables wifi scanning. \
            Empty array in API body for 'wifi' key.")
    parser.add_argument(
        "--no-ble",
        action='store_true',
        help="disables bluetooth scanning. \
            Empty array in API body for 'ble' key.")
    parser.add_argument(
        "--no-mnf",
        action='store_true',
        help="disables manufacturer info from ubus. \
            'unknown' in API body for 'router.mac' \
            and 'router.serial' keys.")
    parser.add_argument(
        "--no-fw",
        action='store_true',
        help="disables firmware info from ubus. \
            'unknown' in API body for 'router.fw' key.")
    parser.add_argument(
        "--no-system",
        action='store_true',
        help="disables bluetooth scanning. \
            'unknown' in API body for 'router.hostname' key.")
    parser.add_argument(
        "--no-timezone",
        action='store_true',
        help="disables timezone info from /etc/config/system. \
            'unknown' in API body for 'router.timezone' key.")
    parser.add_argument(
        "--sender-config-file",
        type=str,
        default=ps.DATA_SENDER_CONFIG_PATH,
        help=f"path to Teltonika Data to Server config file.\
             Default: '{ps.DATA_SENDER_CONFIG_PATH}'")  # noqa
    parser.add_argument(
        "--api-headers",
        type=str,
        default="",
        help="headers to include in the API call. Comma-separated. \
            Overrides default from --query-api-headers --sender-config-file.")
    parser.add_argument(
        "--api-url",
        type=str,
        default="",
        help="HTTP address to POST data to. \
            Overrides default from --query-api-url --sender-config-file.")
    parser.add_argument(
        "--query-api-headers",
        type=str,
        default=ps.DEFAULT_QUERY_API_HEADERS,
        help=f"DPath query to search Data to Server file specified by \
            --sender-config-file for HTTP headers. \
            Error if --api-headers not specified and not found in file.\
            Default: {ps.DEFAULT_QUERY_API_HEADERS}")
    parser.add_argument(
        "--query-api-url",
        type=str,
        default=ps.DEFAULT_QUERY_API_URL,
        help=f"DPath query to search Data to Server file specified by \
            --sender-config-file for an HTTP URL. \
            Error if --api-url not specified and not found in file.\
            Default: {ps.DEFAULT_QUERY_API_URL}")
    parser.add_argument(
        "--ble-wait-s",
        type=int,
        default=UbusBLE.DEFAULT_BLE_WAIT_S,
        help=f"seconds to scan bluetooth before \
            retrieving results. Should be more than ~10s. \
            Default: '{UbusBLE.DEFAULT_BLE_WAIT_S}'")
    parser.add_argument(
        "--is-log-to-console",
        default=ps.IS_LOG_TO_CONSOLE,
        action='store_true',
        help=f"whether to print logs to terminal.\
            Default: '{ps.IS_LOG_TO_CONSOLE}'")
    parser.add_argument(
        "--log-path",
        type=str,
        default=ps.LOG_PATH,
        help=f"filepath to write logs to. Default: '{ps.LOG_PATH}'")
    parser.add_argument(
        "--log-level",
        type=str,
        default=ps.LOG_LEVEL,
        help=f"the lowest level to log. options: \
            {logger.LEVELS}. Default: '{ps.LOG_LEVEL}'")
    parser.add_argument(
        "--log-format",
        type=str,
        default=ps.LOG_FORMAT.replace('%', '%%'),
        help=f"how to format log lines. see: https://docs.python.org/3/library/logging.html#logrecord-attributes. Default: '{ps.LOG_FORMAT.replace('%', '%%')}'")  # noqa
    return parser


def main():
    parser = create_parser()
    config.get_or_write_config(parser)
    args = vars(parser.parse_args(sys.argv[1:]))

    logger.init_logger(**args)
    log.debug("init'd logger.")
    log.debug(f"args: {json.dumps(args, indent=4)}")
    log.debug(f"""args.get("api_url")={args.get("api_url")}""")

    if not args.get("api_url") or not args.get("api_headers"):
        dsr = reader.DataSenderReader(args.get("sender_config_file"))
        dsr.parse()

    # exit error if no API in sender config, unless api-url specified
    if not args.get("api_url"):
        query = args.get("query_api_url")
        args["api_url"] = dsr.search(query)
        if not args["api_url"]:
            log.error(f"specify --api-url \
                      or fix --query-api-url={query}")
            sys.exit(1)
    # exit error if no headers in sender config, unless api-headers specified
    if not args.get("api_headers"):
        query = args.get("query_api_headers")
        args["api_headers"] = dsr.search(query)[0]
        if not args["api_headers"]:
            log.error(f"specify --api-header \
                      or fix --query-api-headers={query}")
            sys.exit(1)

    # make API URL and headers
    api_url = args["api_url"]
    api_headers = args["api_headers"].split(",")
    api_headers = {h.split(":")[0]: h.split(":")[1] for h in api_headers}
    log.debug(f"using API URL: {api_url}")
    log.debug(f"using API headers: {json.dumps(api_headers, indent=4)}")

    # exit error if ubus is not found (we probably aren't on OpenWRT)
    try:
        ubus.Ubus().run_cmd(ubus.Ubus.DEFAULT_RESULT_CMD)
    except CalledProcessError as e:
        if ubus._NO_UBUS_EXC in str(e):
            log.error(ubus._REPLACE_EXC)
            exit(1)

    ble = UbusBLE(wait_s=args["ble_wait_s"])
    wifi = UbusWifi(**args)

    # start scanning in the background (must wait ~10s before retrieving)
    if not args.get("no_ble"):
        ble.scan()

    # do other stuff while we wait
    mnf = UbusMnf()
    fw = UbusFW()
    system = UbusSystem()

    router = {} if args["no_mnf"] else mnf.mac_serial()
    router.update({
        "fw": "unknown" if args["no_fw"] else fw.fw(),
        "hostname": "unknown" if args["no_system"] else system.hostname(),
        "timezone": "unknown" if args["no_timezone"] else sender.get_timezone()
    })
    log.debug(f"got router info: {json.dumps(router, indent=4)}")

    # scan and return wifi within a few seconds
    wifi_devices = [] if args["no_wifi"] else wifi.filtered(wifi.results())
    ble_devices = [] if args["no_ble"] else ble.filtered(ble.results())

    body = {
        "scan": {
            "ble_start_s": int(ble.end_s - ble.elapsed_s),
            "ble_end_s": int(ble.end_s),
            "wifi_start_s": int(wifi.end_s - wifi.elapsed_s),
            "wifi_end_s": int(wifi.end_s),
        },
        "router": router,
        "wifi": wifi_devices,
        "ble": ble_devices,
    }
    log.debug(f"sending body: {json.dumps(body, indent=4)}")

    # Call sender.post_data()
    error, result = sender.post_data(
        url=args["api_url"],
        headers=api_headers,
        data=body)


if __name__ == "__main__":
    main()

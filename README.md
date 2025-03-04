# `sniff`
This project scans bluetooth and wifi signals on a Teltonika RUTX11 network router and sends them via HTTP as JSON to a URL.

# Overview
By default, it does these things:
* searches for existing Teltonika Data to Server config file
  * `/etc/config/data_sender`
  * copies HTTP URL and header by searching for keys
    * `**/http_host`
    * `**/http_header`
* calls `ubus` in subprocesses to gather information
  * wifi
    * `ubus call iwinfo scan '{"device": "wlan1"}'`
  * bluetooth
    * `ubus call blesem scan.start`
    * `ubus call blesem scan.result`
  * firmware
    * `ubus call rut_fota get_info`
  * hostname
    * `ubus call system board`
  * router MAC and serial number
    * `ubus call mnfinfo get`
* grabs timezone info from file or command
    * file `/etc/config/system` if it exists
    * command `date +%Z%z` if file doesn't exist

To disable or override these bahviors, see **Usage** below
  * disable eg. `--no-wifi`, `--no-fw`
  * override defaults
    * `--api-url https://---.com`
    * `--sender-config-file /new/path`

# Installation
we will install this python package to the router as a wheel one of two ways:
1. by downloading from GitLab, uploading via RMS, and installing via router CLI
1. by cloning this git repo and running a devbox command locally

### prerequisites
1. install `python3-pip` on the router if it doesn't exist
    ```console
    root@RUTX11:~# feed=/etc/opkg/openwrt/distfeeds.conf
    root@RUTX11:~# opkg -e "$feed" update
    root@RUTX11:~# opkg -e "$feed" install python3-pip
    ```
1. edit your crontab file to run `sniff` every minute
    ```console
    root@RUTX11:~# crontab -e
    # /etc/crontabs.12317
    * * * * * sniff
    ```

## install to local machine

`devbox run poetry install`

## install via manual upload
1. log in to RMS
    - https://account.rms.teltonika-networks.com
1. download package wheel file from GitLab Release page
    - https://gitlab.com/justinTM/sniff/-/packages/23070661
1. upload package wheel file to RMS
    - https://wiki.teltonika-networks.com/wikibase/index.php?title=RMS_Files&mobileaction=toggle_view_desktop
1. install package via pip
    ```console
    root@RUTX11:~# pip install /var/task/sniff-0.1.0-py3-none-any.whl
    ```

## install via git repo script
1. clone this git repo
    - SSH (if you have a [GitLab SSH token](https://gitlab.com/-/profile/keys))
        ```console
        git clone git@gitlab.com:justinTM/sniff.git
        ```
    - HTTPS (using GitLab username and password or auth token)
        ```console
        git clone https://gitlab.com/justinTM/sniff.git
        ```
1. (optional) download devbox if you don't have it
    - https://www.jetpack.io/devbox
    - devbox is like a makefile, package manager, and virtual environment shell all in one
1. build and upload
    ```console
    devbox run upload <router IP or tailscale name>
    ```

# Usage
```console
root@RUTX11:~# sniff -h
usage: sniff.py [-h] [--no-wifi] [--no-ble] [--no-mnf]
                [--no-fw] [--no-system] [--no-timezone]
                [--sender-config-file SENDER_CONFIG_FILE]
                [--api-headers API_HEADERS]
                [--api-url API_URL]
                [--query-api-headers QUERY_API_HEADERS]
                [--query-api-url QUERY_API_URL]
                [--ble-wait-s BLE_WAIT_S]
                [--is-log-to-console]
                [--log-path LOG_PATH]
                [--log-level LOG_LEVEL]
                [--log-format LOG_FORMAT]

a CLI tool to scan bluetooth and wifi signals from
`ubus` and send to AWS Lambda.

optional arguments:
  -h, --help            show this help message and exit
  --no-wifi             disables wifi scanning. Empty
                        array in API body for 'wifi'
                        key.
  --no-ble              disables bluetooth scanning.
                        Empty array in API body for
                        'ble' key.
  --no-mnf              disables manufacturer info from
                        ubus. 'unknown' in API body for
                        'router.mac' and 'router.serial'
                        keys.
  --no-fw               disables firmware info from
                        ubus. 'unknown' in API body for
                        'router.fw' key.
  --no-system           disables bluetooth scanning.
                        'unknown' in API body for
                        'router.hostname' key.
  --no-timezone         disables timezone info from
                        /etc/config/system. 'unknown' in
                        API body for 'router.timezone'
                        key.
  --sender-config-file SENDER_CONFIG_FILE
                        path to Teltonika Data to Server
                        config file. Default:
                        '/etc/config/data_sender'
  --api-headers API_HEADERS
                        headers to include in the API
                        call. Comma-separated. Overrides
                        default from --query-api-headers
                        --sender-config-file.
  --api-url API_URL     HTTP address to POST data to.
                        Overrides default from --query-
                        api-url --sender-config-file.
  --query-api-headers QUERY_API_HEADERS
                        DPath query to search Data to
                        Server file specified by
                        --sender-config-file for HTTP
                        headers. Error if --api-headers
                        not specified and not found in
                        file. Default: **/http_header
  --query-api-url QUERY_API_URL
                        DPath query to search Data to
                        Server file specified by
                        --sender-config-file for an HTTP
                        URL. Error if --api-url not
                        specified and not found in file.
                        Default: **/http_host
  --ble-wait-s BLE_WAIT_S
                        seconds to scan bluetooth before
                        retrieving results. Should be
                        more than ~10s. Default: '10'
  --is-log-to-console   whether to print logs to
                        terminal. Default: 'False'
  --log-path LOG_PATH   filepath to write logs to.
                        Default: '/var/log/sniff.log'
  --log-level LOG_LEVEL
                        the lowest level to log.
                        options: CRITICAL, FATAL, ERROR,
                        WARN, WARNING, INFO, DEBUG,
                        NOTSET. Default: 'INFO'
  --log-format LOG_FORMAT
                        how to format log lines. see: ht
                        tps://docs.python.org/3/library/
                        logging.html#logrecord-
                        attributes. Default:
                        '%(asctime)s %(levelname)s -
                        %(message)s [%(funcName)s()
                        %(filename)s:%(lineno)d]'
```

# configuration
- after first run of `sniff`, a file `config.ini` will be created in the same directory where you ran it.
- the config file will contain the default arguments, overriden by any flags you may have included in the first run.
- to reset config file to defaults, simply delete file and rerun `sniff`.

    ```ini
    # root@RUTX11:~# cat config.ini
    [DEFAULT]
    no_wifi = False
    no_ble = False
    no_mnf = False
    no_fw = False
    no_system = False
    no_timezone = False
    sender_config_file = /etc/config/data_sender
    api_headers =
    api_url =
    query_api_headers = **/http_header
    query_api_url = **/http_host
    ble_wait_s = 10
    is_log_to_console = False
    log_path = /var/log/sniff.log
    log_level = INFO
    log_format = %%(asctime)s %%(levelname)s - %%(message)s [%%(funcName)s() %%(filename)s:%%(lineno)d]
    ```

# example `sniff` output
```json
    {
        "scan": {
            "ble_start_s": 1708650100,
            "ble_end_s": 1708650140,
            "wifi_start_s": 1708650110,
            "wifi_end_s": 1708650130
        },
        "router": {
            "serial": "unknown",
            "mac": "unknown",
            "fw": "RUTX_R_00.07.06.5",
            "hostname": "RUTX11-3",
            "timezone": "PST8PDT,M3.2.0,M11.1.0"
        },
        "wifi": [
            {
                "quality": 0.31,
                "rssi": -88,
                "host": "Baby Yoda",
                "mac": "01:5A:E3:EB:26:F2"
            }
        ],
        "ble": [
            {
                "rssi": -63,
                "host": "",
                "mac": "73:F7:3E:1C:10:17"
            }
        ]
    }
```

# `devbox`

you can run a few commands to make life easier:


* `upload`
    * build the `sniff` package and install it on a device on your Tailscale tailnet
    * you will be prompted with a list of Teltonika devices/IPs
* `ssh`
    * log in via secure shell to a device on your Tailscale tailnet
    * you will be prompted with a list of Teltonika devices/IPs
    * you can set env var `SNIFF_TS_DEFAULT_IP_ADDRESS` to connect automatically
* `logs`
    * copy the file `/var/log/sniff.log` from device on your Tailscale tailnet
    * you will be prompted with a list of Teltonika devices/IPs
* `scp`
    * copy a file to a device on your Tailscale tailnet
    * you will be prompted with a list of Teltonika devices/IPs
    * optional port arg, e.g. `-p 222`, and positional filename arg

#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only

import os
import configparser

from paths import SCRIPT_PATH

from typing import (
    Optional,
    List,
    Union,
)

CONFIG_PATH = os.path.join(SCRIPT_PATH, "wemod.conf")
DEF_SECTION = "Settings"
CONFIG = configparser.ConfigParser()
CONFIG.optionxform = str
if os.path.exists(CONFIG_PATH):
    CONFIG.read(CONFIG_PATH)


def check_dependencies(requirements_file: str) -> bool:
    from importlib import metadata

    ret = True
    # Check if dependencies have been installed. Use distribution metadata (the
    # pip package name) rather than import_module, because the importable module
    # name often differs from the package name (e.g. PyYAML -> yaml).
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            package = line.split("==")[0].split(">=")[0].split("[")[0].strip()
            try:
                metadata.version(package)
            except metadata.PackageNotFoundError:
                from coreutils import log

                log(f"Package '{package}' is missing")
                ret = False
    return ret


# Read a setting of the config file
def load_conf_setting(
    setting: str, section: str = DEF_SECTION
) -> Optional[str]:
    if section in CONFIG and setting in CONFIG[section]:
        return CONFIG[section][setting]
    return None


# Save a value onto a setting of the config file
def save_conf_setting(
    setting: str, value: Optional[str] = None, section: str = DEF_SECTION
) -> None:
    from coreutils import log

    if not isinstance(section, str):
        log("Error adding the given section: Not a string")
        return
    if section not in CONFIG:
        CONFIG[section] = {}
    if value is None:
        if setting in CONFIG[section]:
            del CONFIG[section][setting]
    elif isinstance(value, str):
        CONFIG[section][setting] = value
    else:
        log("Error saving given value: Not a string or None")
        return
    # Write atomically: write to a temp file and rename over the target so a
    # crash or a second concurrent instance can't truncate/corrupt the config.
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as configfile:
        CONFIG.write(configfile)
    os.replace(tmp_path, CONFIG_PATH)


def read_file(version_file: str) -> Optional[str]:  # read file
    try:
        with open(version_file, "r") as file:
            return file.read().strip()
    except Exception as e:
        return None


def parse_version(
    version_str: Optional[Union[list, str]] = None,
) -> Optional[List[int]]:
    if version_str and isinstance(version_str, str):
        # Replace '-' with '.' and ',' with '.'
        numbers = version_str.replace("-", ".").replace(",", ".")

        # Clean up number
        majornumber = None
        minornumber = None
        addat = 0
        currentnumber = ""
        for number in numbers:
            if number and number.isnumeric():
                currentnumber += str(number)
                if currentnumber:
                    if addat == 0:
                        majornumber = currentnumber
                    elif addat == 1:
                        minornumber = currentnumber
            elif number and number == "." and currentnumber and addat == 0:
                addat = 1
                currentnumber = ""

        if not minornumber:
            minornumber = "0"
        if len(minornumber.lstrip("0")) > 2:
            minornumber = minornumber.lstrip("0")
            if len(minornumber) > 3:
                minornumber = minornumber[:2]
            else:
                minornumber = minornumber[:1]

        if majornumber and minornumber:  # Return numbers if set
            return [int(majornumber), int(minornumber)]
        else:
            return None

    elif isinstance(version_str, list):
        return version_str
    return None


def winpath(path: str, dobble: bool = True, addfront: str = "Z:") -> str:
    if dobble:
        return addfront + path.replace(os.sep, "\\\\")
    else:
        return addfront + path.replace(os.sep, "\\")


def split_list_by_delimiter(
    input_list: List[str], delimiter: str
) -> List[List[str]]:
    result = []
    current_sublist = []
    for item in input_list:
        if item == delimiter:
            if current_sublist:
                result.append(current_sublist)
                current_sublist = []
        else:
            current_sublist.append(item)
    if current_sublist:
        result.append(current_sublist)
    return result


def join_lists_with_delimiter(
    sublists: List[List[str]], delimiter: Optional[str] = None
) -> List[str]:
    result = []
    for sublist in sublists:
        result.extend(sublist)
        if delimiter is not None:
            result.append(delimiter)
    if delimiter is not None and result:
        result.pop()  # Remove the last delimiter if delimiter is not None
    return result


# Check if a string contains a url protocol
def contains_url_protocol(s: str) -> bool:
    parts = s.split("://")
    if len(parts) < 2:
        return False

    protocol = parts[0]
    return protocol.isalnum() and len(protocol) > 1


def is_exe_or_forced(s: str) -> bool:
    env_val = os.getenv("NO_EXE")
    if env_val:  # check env
        if env_val.lower() == "false":
            return True  # we want game exe, so true
        elif env_val.lower() == "none":
            pass  # none is to just ignore
        else:
            return False  # assume since set, user wanted to NO exe

    cfg_val = load_conf_setting("NoEXE")
    if cfg_val:  # same check with conf
        if cfg_val.lower() == "false":
            return True
        elif cfg_val.lower() == "none":
            pass
        else:
            return False

    # final check if not url its a exe
    return not contains_url_protocol(s)

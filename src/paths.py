#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only

"""Shared resolution of the launcher's on-disk location.

Every module used to duplicate the PyInstaller-aware ``__file__`` /
``sys.executable`` dance. This module is the single source of truth for the
script path and the project base directory, so the logic lives in one place.

It only depends on the standard library, so any module (including the
dependency-free ``corenodep``) can import it without creating cycles.
"""

import os
import sys


def _resolve_script_file() -> str:
    # When frozen by PyInstaller, __file__ points inside the bundle; use the
    # real executable instead.
    if getattr(sys, "frozen", False):
        return os.path.realpath(sys.executable)
    return os.path.realpath(__file__)


# Absolute path of the running script/executable.
SCRIPT_IMP_FILE = _resolve_script_file()
# Directory that contains the script (the ``src`` folder in a source checkout).
SCRIPT_PATH = os.path.dirname(SCRIPT_IMP_FILE)
# Project root: the parent of ``src`` when running from a source checkout.
if os.path.basename(SCRIPT_PATH) == "src":
    SCRIPT_BASE = os.path.dirname(SCRIPT_PATH)
else:
    SCRIPT_BASE = SCRIPT_PATH

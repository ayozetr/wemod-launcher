# SPDX-License-Identifier: AGPL-3.0-only
"""Make the modules under src/ importable from the tests."""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC))

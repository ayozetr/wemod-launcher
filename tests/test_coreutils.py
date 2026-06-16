# SPDX-License-Identifier: AGPL-3.0-only
"""Unit tests for the pure helpers in coreutils."""

import coreutils


class TestVersionTuple:
    def test_two_components(self):
        assert coreutils._version_tuple("1.540") == (1, 540)

    def test_three_components(self):
        assert coreutils._version_tuple("1.5.4") == (1, 5, 4)

    def test_ordering(self):
        assert coreutils._version_tuple("1.540") > coreutils._version_tuple(
            "1.539"
        )
        assert coreutils._version_tuple("1.5.4") > coreutils._version_tuple(
            "1.5"
        )

    def test_non_numeric_returns_none(self):
        assert coreutils._version_tuple("1.x") is None
        assert coreutils._version_tuple("abc") is None
        assert coreutils._version_tuple(None) is None

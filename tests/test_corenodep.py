# SPDX-License-Identifier: AGPL-3.0-only
"""Unit tests for the dependency-free helpers in corenodep."""

import corenodep


class TestParseVersion:
    def test_major_and_minor(self):
        assert corenodep.parse_version("8.0") == [8, 0]
        assert corenodep.parse_version("PfxVer8.26") == [8, 26]
        assert corenodep.parse_version("GE-Proton9-20") == [9, 20]

    def test_major_only_does_not_crash(self):
        # Regression: these used to raise AttributeError because the missing
        # minor became int 0 and .lstrip was called on it.
        assert corenodep.parse_version("v9") == [9, 0]
        assert corenodep.parse_version("7") == [7, 0]
        assert corenodep.parse_version("9") == [9, 0]
        assert corenodep.parse_version("GE-Proton9") == [9, 0]

    def test_no_number_returns_none(self):
        assert corenodep.parse_version("GE-Proton") is None
        assert corenodep.parse_version("abc") is None
        assert corenodep.parse_version("") is None
        assert corenodep.parse_version(None) is None

    def test_list_passthrough(self):
        assert corenodep.parse_version([8, 26]) == [8, 26]


class TestWinpath:
    def test_double_backslash_default(self):
        assert (
            corenodep.winpath("/Game/game.exe", addfront="")
            == "\\\\Game\\\\game.exe"
        )

    def test_single_backslash(self):
        assert (
            corenodep.winpath("/Game/game.exe", dobble=False, addfront="")
            == "\\Game\\game.exe"
        )

    def test_default_drive_prefix(self):
        assert corenodep.winpath("/a", dobble=False).startswith("Z:")


class TestListDelimiters:
    def test_split_by_delimiter(self):
        assert corenodep.split_list_by_delimiter(
            ["a", "b", "--", "c"], "--"
        ) == [["a", "b"], ["c"]]

    def test_split_drops_empty_sublists(self):
        assert corenodep.split_list_by_delimiter(
            ["--", "a", "--", "--", "b"], "--"
        ) == [["a"], ["b"]]

    def test_join_with_delimiter(self):
        assert corenodep.join_lists_with_delimiter(
            [["a", "b"], ["c"]], "--"
        ) == ["a", "b", "--", "c"]

    def test_join_without_delimiter(self):
        assert corenodep.join_lists_with_delimiter(
            [["a"], ["b"]]
        ) == ["a", "b"]

    def test_split_join_roundtrip(self):
        original = [["proton", "run"], ["game.exe"]]
        joined = corenodep.join_lists_with_delimiter(original, "--")
        assert corenodep.split_list_by_delimiter(joined, "--") == original

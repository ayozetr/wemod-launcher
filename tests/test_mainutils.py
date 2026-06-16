# SPDX-License-Identifier: AGPL-3.0-only
"""Unit tests for the version-matching logic in mainutils."""

import mainutils


def _release(tag, url):
    return {"tag_name": tag, "assets": [{"browser_download_url": url}]}


class TestFindClosestCompatibleRelease:
    def test_exact_match_wins(self):
        releases = [
            _release("PfxVer8.26", "u-826"),
            _release("PfxVer9.0", "u-90"),
        ]
        version, url = mainutils.find_closest_compatible_release(
            releases, [8, 26]
        )
        assert version == [8, 26]
        assert url == "u-826"

    def test_same_major_lower_minor_preferred_over_other_major(self):
        releases = [
            _release("PfxVer8.10", "u-810"),
            _release("PfxVer7.40", "u-740"),
        ]
        version, url = mainutils.find_closest_compatible_release(
            releases, [8, 26]
        )
        # Same major (8) should win over a different major (7).
        assert version == [8, 10]
        assert url == "u-810"

    def test_non_pfxver_tags_ignored(self):
        releases = [
            _release("v1.2.3", "u-ignored"),
            _release("PfxVer8.26", "u-826"),
        ]
        version, url = mainutils.find_closest_compatible_release(
            releases, [8, 26]
        )
        assert version == [8, 26]
        assert url == "u-826"

    def test_no_releases_returns_none(self):
        version, url = mainutils.find_closest_compatible_release([], [8, 26])
        assert version is None
        assert url is None

    def test_release_without_assets_is_skipped(self):
        releases = [
            {"tag_name": "PfxVer8.26", "assets": []},  # no asset -> skip
            _release("PfxVer8.26", "u-826"),
        ]
        version, url = mainutils.find_closest_compatible_release(
            releases, [8, 26]
        )
        assert version == [8, 26]
        assert url == "u-826"


class TestPathUnderPrefix:
    def test_exact_match(self):
        assert mainutils._path_under_prefix("version", "version") is True

    def test_contained(self):
        assert (
            mainutils._path_under_prefix(
                "pfx/drive_c/users/foo", "pfx/drive_c/users"
            )
            is True
        )

    def test_sibling_with_shared_string_prefix_excluded(self):
        # The old commonprefix-by-character matched this; component matching
        # must not.
        assert (
            mainutils._path_under_prefix(
                "pfx/drive_c/Program Files X/foo", "pfx/drive_c/Program Files"
            )
            is False
        )

    def test_partial_name_excluded(self):
        assert mainutils._path_under_prefix("versionfoo", "version") is False

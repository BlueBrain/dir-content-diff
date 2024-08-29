"""Test the MorphIO extensions of the ``dir-content-diff`` package."""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import re

import pytest

import dir_content_diff
import dir_content_diff.comparators.morphio

try:
    from morphio import Morphology
except ImportError:
    pass


class TestRegistry:
    """Test the internal registry."""

    def test_morphology_register(self, registry_reseter):
        """Test registering the morphologies plugin."""
        assert ".asc" not in dir_content_diff.get_comparators()
        assert ".h5" not in dir_content_diff.get_comparators()
        assert ".swc" not in dir_content_diff.get_comparators()

        dir_content_diff.comparators.morphio.register()

        for ext in [".asc", ".h5", ".swc"]:
            assert (
                dir_content_diff.get_comparators()[ext]
                == dir_content_diff.comparators.morphio.MorphologyComparator()
            )


@pytest.fixture
def morph_1(tmp_path):
    """Create a simple morphology and return its file path."""
    contents = """1 1 0 4 0 3.0 -1
                  2 3 0 0 2 0.5 1
                  3 3 0 0 3 0.5 2
                  4 3 0 0 4 0.5 3
                  5 3 0 0 5 0.5 4"""
    morph = Morphology(contents, "swc")
    filename = tmp_path / "morph_1.swc"
    morph.as_mutable().write(filename)
    return filename


@pytest.fixture
def morph_2(tmp_path):
    """Create a simple morphology and return its file path."""
    contents = """1 1 0 4 0 3.0 -1
                  2 3 0 0 2 0.5 1
                  3 3 0 0 3 0.5 2
                  4 3 0 0 4 999 3
                  5 3 0 0 999 0.5 4"""
    morph = Morphology(contents, "swc")
    filename = tmp_path / "morph_2.swc"
    morph.as_mutable().write(filename)
    return filename


def test_comparator_equal(morph_1):
    """Test the comparator on two equal morphologies."""
    comparator = dir_content_diff.comparators.morphio.MorphologyComparator()
    assert not comparator(morph_1, morph_1)


def test_comparator_diff(morph_1, morph_2):
    """Test the comparator on two different morphologies."""
    comparator = dir_content_diff.comparators.morphio.MorphologyComparator()
    diff = comparator(morph_1, morph_2)
    match_res = re.match(
        r"""The files '\S*' and '\S*' are different:\n"""
        r"""Attributes Section\.points of:\n"""
        r"""Section\(id=0, points=\[\(0 0 2\),\.\.\., \(0 0 5\)\]\)\n"""
        r"""Section\(id=0, points=\[\(0 0 2\),\.\.\., \(0 0 999\)\]\)\n"""
        r"""have the same shape but different values\n"""
        r"""Vector points differs at index 3: \[0\. 0\. 5\.\] != \[  0\.   0\. 999\.\]""",
        diff,
    )
    assert match_res is not None

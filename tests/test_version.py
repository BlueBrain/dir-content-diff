"""Test the version of the ``dir-content-diff`` package."""
from importlib.metadata import version

import dir_content_diff


def test_version():
    """Test the version of the dir-content-diff package."""
    pkg_version = version("dir-content-diff")
    assert dir_content_diff.__version__ == pkg_version

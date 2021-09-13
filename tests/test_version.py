"""Test the version of the ``dir-content-diff`` package."""
import pkg_resources

import dir_content_diff


def test_version():
    """Test the version of the dir-content-diff package."""
    pkg_version = pkg_resources.get_distribution("dir-content-diff").version
    assert dir_content_diff.__version__ == pkg_version

"""Plugin for pytest.

Register this package as a pytest plugin. When run with pytest, the
:func:`dir_content_diff.assert_equal_trees` function can use the following command line options of
pytest:

* ``--dcd-export-formatted-data`` to trigger the export of the formatted files.
* ``--dcd-export-suffix`` to specify a custom suffix (the default is ``_FORMATTED``).

When this feature is triggered, the files that are processed by a comparator with a ``save``
capability will be formatted and exported to a directory whose name is built from the compared
directory with a suffix added. The default suffix is ``_FORMATTED`` and can be customized.
"""
from dir_content_diff import _DEFAULT_EXPORT_SUFFIX
from dir_content_diff import assert_equal_trees


def pytest_addoption(parser):
    """Add command line options for pytest."""
    group = parser.getgroup("dir-content-diff", "dir-content-diff integration")
    group.addoption(
        "--dcd-export-formatted-data",
        action="store_true",
        default=False,
        help=(
            "Format the data and export it to a new directory whose name is the reference "
            "directory name and a given suffix."
        ),
    )
    group.addoption(
        "--dcd-export-suffix",
        default=_DEFAULT_EXPORT_SUFFIX,
        help="Suffix added to the reference directory.",
    )


def pytest_configure(config):
    """Process cmdline arguments."""
    # pylint: disable=protected-access
    assert_equal_trees._pytest_export_formatted_data = config.getoption(
        "--dcd-export-formatted-data"
    )
    assert_equal_trees._pytest_export_suffix = config.getoption("--dcd-export-suffix")

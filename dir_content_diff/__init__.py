"""Module containing the base functions of the dir-content-diff package."""
import copy
import logging
from pathlib import Path

from dir_content_diff.base_comparators import DefaultComparator
from dir_content_diff.base_comparators import JsonComparator
from dir_content_diff.base_comparators import PdfComparator
from dir_content_diff.base_comparators import YamlComparator
from dir_content_diff.util import diff_msg_formatter
from dir_content_diff.util import format_ext
from dir_content_diff.version import VERSION as __version__  # noqa

L = logging.getLogger(__name__)


_DEFAULT_COMPARATORS = {
    None: DefaultComparator(),
    ".json": JsonComparator(),
    ".pdf": PdfComparator(),
    ".yaml": YamlComparator(),
    ".yml": YamlComparator(),
}

_COMPARATORS = {}


def reset_comparators():
    """Reset the comparator registry to the default values."""
    global _COMPARATORS  # pylint: disable=global-statement
    _COMPARATORS = copy.deepcopy(_DEFAULT_COMPARATORS)


reset_comparators()


def get_comparators():
    """Return a copy of the comparator registry."""
    return copy.deepcopy(_COMPARATORS)


def register_comparator(ext, comparator, force=False):
    """Add a comparator to the registry.

    Args:
        ext (str): The extension to register.
        comparator (callable): The comparator that should be associated with the given extension.
        force (bool): If set to `True`, no exception is raised if the given `ext` is already
            registered.

    .. note::
        The given comparator should have the following signature:

        .. code-block:: python

            comparator(
                ref_file: str,
                comp_file: str,
                *diff_args: Sequence[Any],
                return_raw_diffs: bool=False,
                **diff_kwargs: Mapping[str, Any],
            ) -> Union[False, str]

        The return type can be Any when used with `return_raw_diffs == True`.
    """
    ext = format_ext(ext)
    if not force and ext in _COMPARATORS:
        raise ValueError(
            f"The '{ext}' extension is already registered and must be unregistered before being "
            "replaced."
        )
    _COMPARATORS[ext] = comparator


def unregister_comparator(ext, quiet=False):
    """Remove a comparator from the registry.

    Args:
        ext (str): The extension to unregister.
        quiet (bool): If set to `True`, no exception is raised if the given `ext` is not
            registered.

    Returns:
        The removed comparator.
    """
    ext = format_ext(ext)
    if not quiet and ext not in _COMPARATORS:
        raise ValueError(f"The '{ext}' extension is not registered.")
    return _COMPARATORS.pop(ext, None)


def compare_files(ref_file, comp_file, comparator, *args, return_raw_diffs=False, **kwargs):
    """Compare 2 files and return the difference.

    Args:
        ref_file (str): Path to the reference file.
        comp_file (str): Path to the compared file.
        comparator (callable): The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        return_raw_diffs (bool): If set to True, only the raw differences are returned instead of a
            formatted report.
        *args: passed to the comparator.
        **kwargs: passed to the comparator.

    Returns:
        bool or str: False if the files are equal or a string with a message explaining the
        differences if they are different.
    """
    # Get the compared file
    L.debug("Compare: %s and %s", ref_file, comp_file)

    if comparator is None:
        # If the suffix has no associated comparator, use the default comparator
        comparator = _COMPARATORS.get(None)

    try:
        return comparator(ref_file, comp_file, *args, return_raw_diffs=return_raw_diffs, **kwargs)
    except Exception as exception:  # pylint: disable=broad-except
        return diff_msg_formatter(
            ref_file,
            comp_file,
            reason="Exception raised: " + "\n".join(exception.args),
            args=args,
            kwargs=kwargs,
        )


def compare_trees(
    ref_path, comp_path, comparators=None, specific_args=None, return_raw_diffs=False
):
    """Compare all files from 2 different directory trees and return the differences.

    .. note::

        The comparison only considers the files found in the reference directory. So if there are
        files in the compared directory that do not exist in the reference directory, they are just
        ignored.

    Args:
        ref_path (str): Path to the reference directory.
        comp_path (str): Path to the directory that must be compared against the reference.
        comparators (dict): A dict to override the registered comparators.
        specific_args (dict): A dict with the args/kwargs that should be given to the comparator
            for a given file. This dict should be like the following:

            .. code-block:: Python

                {
                    <relative_file_path>: {
                        args: [arg1, arg2, ...],
                        kwargs: {
                            kwarg_name_1: kwarg_value_1,
                            kwarg_name_2: kwarg_value_2,
                        }
                    },
                    <another_file_path>: {...}
                }
        return_raw_diffs (bool): If set to True, only the raw differences are returned instead of a
            formatted report.

    Returns:
        dict: A dict in which the keys are the relative file paths and the values are the
        difference messages. If the directories are considered as equal, an empty dict is
        returned.
    """
    if comparators is None:
        comparators = _COMPARATORS

    ref_path = Path(ref_path)
    comp_path = Path(comp_path)

    if specific_args is None:
        specific_args = {}

    # Loop over all files and call the correct comparator
    different_files = {}
    for ref_file in ref_path.glob("**/*"):
        if ref_file.is_dir():
            continue

        relative_path = ref_file.relative_to(ref_path).as_posix()
        comp_file = comp_path / relative_path

        if comp_file.exists():
            specific_file_args = specific_args.get(relative_path, {})
            res = compare_files(
                ref_file,
                comp_file,
                comparators.get(ref_file.suffix),
                *specific_file_args.get("args", []),
                return_raw_diffs=return_raw_diffs,
                **specific_file_args.get("kwargs", {}),
            )
            if res is not False:
                different_files[relative_path] = res
        else:
            msg = f"The file '{relative_path}' does not exist in '{comp_path}'."
            different_files[relative_path] = msg

    return different_files


def assert_equal_trees(*args, **kwargs):
    """Raise an :class:`AssertionError` if differences are found in the two directory trees.

    See the :func:`compare_trees` function for details on arguments as this function just calls it.
    """
    different_files = compare_trees(*args, **kwargs)

    # Sort the files according to their relative paths
    sorted_items = sorted(different_files.items(), key=lambda x: x[0])

    # Test that all files are equal and raise the formatted messages if there are differences
    assert len(different_files) == 0, "\n\n\n".join([i[1] for i in sorted_items])

    # Return True if the trees are equal
    return True

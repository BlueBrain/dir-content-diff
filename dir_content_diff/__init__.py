"""dir-content-diff package.

Simple tool to compare directory contents.
"""
import copy
import importlib.metadata
import logging
import re
from pathlib import Path

from dir_content_diff.base_comparators import DefaultComparator
from dir_content_diff.base_comparators import IniComparator
from dir_content_diff.base_comparators import JsonComparator
from dir_content_diff.base_comparators import PdfComparator
from dir_content_diff.base_comparators import XmlComparator
from dir_content_diff.base_comparators import YamlComparator
from dir_content_diff.util import diff_msg_formatter
from dir_content_diff.util import format_ext

__version__ = importlib.metadata.version("dir-content-diff")

L = logging.getLogger(__name__)


_DEFAULT_COMPARATORS = {
    None: DefaultComparator(),
    ".cfg": IniComparator(),  # luigi config files
    ".conf": IniComparator(),  # logging config files
    ".ini": IniComparator(),
    ".json": JsonComparator(),
    ".pdf": PdfComparator(),
    ".yaml": YamlComparator(),
    ".yml": YamlComparator(),
    ".xml": XmlComparator(),
}

_DEFAULT_EXPORT_SUFFIX = "_FORMATTED"

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
        force (bool): If set to ``True``, no exception is raised if the given ``ext`` is already
            registered and the comparator is replaced.

    .. note::
        It is possible to create and register custom comparators. The easiest way to do it is to
        derive a class from :class:`dir_content_diff.BaseComparator`.

        Otherwise, the given comparator should be a callable with the following signature:

        .. code-block:: python

            comparator(
                ref_file: str,
                comp_file: str,
                *diff_args: Sequence[Any],
                return_raw_diffs: bool=False,
                **diff_kwargs: Mapping[str, Any],
            ) -> Union[False, str]

        The return type can be Any when used with `return_raw_diffs == True`, else it should be a
        string object.
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
        quiet (bool): If set to ``True``, no exception is raised if the given ``ext`` is not
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
        return_raw_diffs (bool): If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        *args: passed to the comparator.
        **kwargs: passed to the comparator.

    Returns:
        bool or str: ``False`` if the files are equal or a string with a message explaining the
        differences if they are different.
    """
    # Get the compared file
    L.debug("Compare: %s and %s", ref_file, comp_file)

    try:
        return comparator(ref_file, comp_file, *args, return_raw_diffs=return_raw_diffs, **kwargs)
    except Exception as exception:  # pylint: disable=broad-except
        load_kwargs = kwargs.pop("load_kwargs", None)
        format_data_kwargs = kwargs.pop("format_data_kwargs", None)
        filter_kwargs = kwargs.pop("filter_kwargs", None)
        format_diff_kwargs = kwargs.pop("format_diff_kwargs", None)
        sort_kwargs = kwargs.pop("sort_kwargs", None)
        concat_kwargs = kwargs.pop("concat_kwargs", None)
        report_kwargs = kwargs.pop("report_kwargs", None)
        try:
            exception_args = "\n".join(str(i) for i in exception.args)
        except Exception:  # pylint: disable=broad-exception-caught
            exception_args = "UNKNOWN ERROR: Could not get information from the exception"
        exc_type = type(exception).__name__
        return diff_msg_formatter(
            ref_file,
            comp_file,
            reason=f"Exception raised: ({exc_type}) {exception_args}",
            diff_args=args,
            diff_kwargs=kwargs,
            load_kwargs=load_kwargs,
            format_data_kwargs=format_data_kwargs,
            filter_kwargs=filter_kwargs,
            format_diff_kwargs=format_diff_kwargs,
            sort_kwargs=sort_kwargs,
            concat_kwargs=concat_kwargs,
            report_kwargs=report_kwargs,
        )


def export_formatted_file(file, formatted_file, comparator, **kwargs):
    """Format a data file and export it.

    .. note:: A new file is created only if the corresponding comparator has saving capability.

    Args:
        file (str): Path to the compared file.
        formatted_file (str): Path to the formatted file.
        comparator (callable): The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        **kwargs: Can contain the following dictionaries: 'load_kwargs', 'format_data_kwargs' and
            'save_kwargs'.
    """
    if hasattr(comparator, "save_capability") and comparator.save_capability:
        # pylint: disable=protected-access
        L.debug("Format: %s into %s", file, formatted_file)
        data = comparator.load(
            file,
            **kwargs.get(
                "load_kwargs",
                comparator._default_load_kwargs
                if hasattr(comparator, "_default_load_kwargs")
                else {},
            ),
        )
        formatted_data = comparator.format_data(
            data,
            **kwargs.get(
                "format_data_kwargs",
                comparator._default_format_data_kwargs
                if hasattr(comparator, "_default_format_data_kwargs")
                else {},
            ),
        )
        Path(formatted_file).parent.mkdir(parents=True, exist_ok=True)
        comparator.save(
            formatted_data,
            formatted_file,
            **kwargs.get(
                "save_kwargs",
                comparator._default_save_kwargs
                if hasattr(comparator, "_default_save_kwargs")
                else {},
            ),
        )
    else:
        L.info("Skip formatting for '%s' because the comparator has no saving capability.", file)


def compare_trees(
    ref_path,
    comp_path,
    comparators=None,
    specific_args=None,
    return_raw_diffs=False,
    export_formatted_files=False,
):
    """Compare all files from 2 different directory trees and return the differences.

    .. note::

        The comparison only considers the files found in the reference directory. So if there are
        files in the compared directory that do not exist in the reference directory, they are just
        ignored.

    Args:
        ref_path (str): Path to the reference directory.
        comp_path (str): Path to the directory that must be compared against the reference.
        comparators (dict): A ``dict`` to override the registered comparators.
        specific_args (dict): A ``dict`` with the args/kwargs that should be given to the
            comparator for a given file. This ``dict`` should be like the following:

            .. code-block:: Python

                {
                    <relative_file_path>: {
                        comparator: ComparatorInstance,
                        args: [arg1, arg2, ...],
                        kwargs: {
                            kwarg_name_1: kwarg_value_1,
                            kwarg_name_2: kwarg_value_2,
                        }
                    },
                    <another_file_path>: {...},
                    <a name for this category>: {
                        "patterns": ["regex1", "regex2", ...],
                        ... (other arguments)
                    }
                }

            If the "patterns" entry is present, then the name is not considered and is only used as
            a helper for the user. When a "patterns" entry is detected, the other arguments are
            applied to all files whose relative name matches one of the given regular expression
            patterns. If a file could match multiple patterns of different groups, only the first
            one is considered.

            Note that all entries in this ``dict`` are optional.
        return_raw_diffs (bool): If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        export_formatted_files (bool or str): If set to ``True`` or a not empty string, create a
            new directory with formatted compared data files. If a string is passed, this string is
            used as suffix for the new directory. If `True` is passed, the suffix is
            ``_FORMATTED``.

    Returns:
        dict: A ``dict`` in which the keys are the relative file paths and the values are the
        difference messages. If the directories are considered as equal, an empty ``dict`` is
        returned.
    """
    if comparators is None:
        comparators = _COMPARATORS

    ref_path = Path(ref_path)
    comp_path = Path(comp_path)
    formatted_data_path = comp_path.with_name(
        comp_path.name
        + (
            export_formatted_files
            if (export_formatted_files is not True and export_formatted_files)
            else _DEFAULT_EXPORT_SUFFIX
        )
    )

    if specific_args is None:
        specific_args = {}
    else:
        specific_args = copy.deepcopy(specific_args)

    pattern_specific_args = {}
    for v in specific_args.values():
        for pattern in v.pop("patterns", []):
            pattern_specific_args[re.compile(pattern)] = v

    # Loop over all files and call the correct comparator
    different_files = {}
    for ref_file in ref_path.glob("**/*"):
        if ref_file.is_dir():
            continue

        relative_path = ref_file.relative_to(ref_path).as_posix()
        comp_file = comp_path / relative_path

        if comp_file.exists():
            specific_file_args = specific_args.get(relative_path, None)
            if specific_file_args is None:
                for pattern, pattern_args in pattern_specific_args.items():
                    if pattern.match(relative_path):
                        specific_file_args = copy.deepcopy(pattern_args)
                        break
            if specific_file_args is None:
                specific_file_args = {}
            comparator = specific_file_args.pop(
                "comparator",
                comparators.get(
                    ref_file.suffix,
                    _COMPARATORS.get(None),
                ),
            )
            comparator_args = specific_file_args.pop("args", [])
            res = compare_files(
                ref_file,
                comp_file,
                comparator,
                *comparator_args,
                return_raw_diffs=return_raw_diffs,
                **specific_file_args,
            )
            if res is not False:
                different_files[relative_path] = res
            if export_formatted_files is not False:
                export_formatted_file(
                    comp_file,
                    formatted_data_path / relative_path,
                    comparator,
                    **specific_file_args,
                )
        else:
            msg = f"The file '{relative_path}' does not exist in '{comp_path}'."
            different_files[relative_path] = msg

    return different_files


def assert_equal_trees(*args, export_formatted_files=False, **kwargs):
    """Raise an :class:`AssertionError` if differences are found in the two directory trees.

    .. note::
        This function has a specific behavior when run with pytest. See the doc of the
        :mod:`dir_content_diff.pytest_plugin`.

    Args:
        *args: passed to the :func:`compare_trees` function.
        export_formatted_files (bool, or str): If set to ``True``, the formatted files are exported
            to the directory with the default suffix. If set to a string, it is used as suffix for
            the new directory.
        **kwargs: passed to the :func:`compare_trees` function.

    Returns:
        (bool) ``True`` if the trees are equal. If they are not, an :class:`AssertionError` is
        raised.
    """
    # If run with pytest, get the trigger to export formatted data from it
    if export_formatted_files is False and hasattr(
        assert_equal_trees, "_pytest_export_formatted_data"
    ):
        # pylint: disable=no-member
        # pylint: disable=protected-access
        export_formatted_files = assert_equal_trees._pytest_export_formatted_data
        if export_formatted_files is True and assert_equal_trees._pytest_export_suffix:
            export_formatted_files = assert_equal_trees._pytest_export_suffix

    different_files = compare_trees(*args, export_formatted_files=export_formatted_files, **kwargs)

    # Sort the files according to their relative paths
    sorted_items = sorted(different_files.items(), key=lambda x: x[0])
    # Test that all files are equal and raise the formatted messages if there are differences
    if len(sorted_items) > 0:
        raise AssertionError("\n\n\n".join([i[1] for i in sorted_items]))

    # Return True if the trees are equal
    return True

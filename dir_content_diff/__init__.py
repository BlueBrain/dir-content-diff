"""dir-content-diff package.

Simple tool to compare directory contents.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import copy
import importlib.metadata
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import Union

import attrs

from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.base_comparators import DefaultComparator
from dir_content_diff.base_comparators import IniComparator
from dir_content_diff.base_comparators import JsonComparator
from dir_content_diff.base_comparators import PdfComparator
from dir_content_diff.base_comparators import XmlComparator
from dir_content_diff.base_comparators import YamlComparator
from dir_content_diff.util import LOGGER
from dir_content_diff.util import diff_msg_formatter
from dir_content_diff.util import format_ext

# Type alias for comparators
ComparatorType = Union[BaseComparator, Callable]

__version__ = importlib.metadata.version("dir-content-diff")

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


def register_comparator(
    ext: str, comparator: ComparatorType, force: bool = False
) -> None:
    """Add a comparator to the registry.

    Args:
        ext: The extension to register.
        comparator: The comparator that should be associated with the given extension.
        force: If set to ``True``, no exception is raised if the given ``ext`` is already
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


def unregister_comparator(ext: str, quiet: bool = False):
    """Remove a comparator from the registry.

    Args:
        ext: The extension to unregister.
        quiet: If set to ``True``, no exception is raised if the given ``ext`` is not
            registered.

    Returns:
        The removed comparator.
    """
    ext = format_ext(ext)
    if not quiet and ext not in _COMPARATORS:
        raise ValueError(f"The '{ext}' extension is not registered.")
    return _COMPARATORS.pop(ext, None)


def _convert_iterable_to_tuple(
    x: Optional[Iterable[str]],
) -> Optional[Tuple[str, ...]]:
    """Convert an iterable to a tuple, or return None."""
    if x is None:
        return None
    return tuple(x)


def _validate_specific_args(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate specific_args structure."""
    for file_path, args in value.items():
        if not isinstance(args, dict):
            raise ValueError(f"specific_args['{file_path}'] must be a dictionary")
        # Note: regex patterns in specific_args will be validated during compilation
        # in __attrs_post_init__, so no need to validate them here


def _validate_export_formatted_files(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate export_formatted_files is either bool or non-empty string."""
    if isinstance(value, str) and len(value.strip()) == 0:
        raise ValueError(
            "export_formatted_files must be a non-empty string when provided as string"
        )


def _validate_comparators(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate comparators are either BaseComparator instances or callable."""
    for ext, comparator in value.items():
        if not (isinstance(comparator, BaseComparator) or callable(comparator)):
            raise ValueError(
                f"Comparator for extension '{ext}' must be a BaseComparator instance "
                "or callable"
            )


@attrs.frozen
class ComparisonConfig:
    """Configuration class to store comparison settings.

    Attributes:
        include_patterns: A list of regular expression patterns. If the relative path of a
            file does not match any of these patterns, it is ignored during the comparison. Note
            that this means that any specific arguments for that file will also be ignored.
        exclude_patterns: A list of regular expression patterns. If the relative path of a
            file matches any of these patterns, it is ignored during the comparison. Note that
            this means that any specific arguments for that file will also be ignored.
        comparators: A ``dict`` to override the registered comparators.
        specific_args: A ``dict`` with the args/kwargs that should be given to the
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
        return_raw_diffs: If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        export_formatted_files: If set to ``True`` or a not empty string, create a
            new directory with formatted compared data files. If a string is passed, this string is
            used as suffix for the new directory. If `True` is passed, the suffix is
            ``_FORMATTED``.
    """

    include_patterns: Optional[Iterable[str]] = attrs.field(
        default=None, converter=_convert_iterable_to_tuple
    )
    exclude_patterns: Optional[Iterable[str]] = attrs.field(
        default=None, converter=_convert_iterable_to_tuple
    )
    comparators: Optional[Dict[Optional[str], ComparatorType]] = attrs.field(
        default=None, validator=attrs.validators.optional(_validate_comparators)
    )
    specific_args: Optional[Dict[str, Dict[str, Any]]] = attrs.field(
        default=None, validator=attrs.validators.optional(_validate_specific_args)
    )
    return_raw_diffs: bool = attrs.field(default=False)
    export_formatted_files: Union[bool, str] = attrs.field(
        default=False, validator=_validate_export_formatted_files
    )

    # Compiled patterns - computed once, no caching complexity needed
    compiled_include_patterns: Tuple[Pattern[str], ...] = attrs.field(init=False)
    compiled_exclude_patterns: Tuple[Pattern[str], ...] = attrs.field(init=False)
    pattern_specific_args: Dict[Pattern[str], Dict[str, Any]] = attrs.field(
        init=False, repr=False
    )

    def __attrs_post_init__(self):
        """Initialize computed fields after attrs initialization."""
        # Validate and compile patterns - with frozen, we compile once and store directly
        try:
            compiled_include = self._compile_patterns(self.include_patterns)
            object.__setattr__(self, "compiled_include_patterns", compiled_include)
        except ValueError as e:
            raise ValueError(f"Error in include_patterns: {e}") from e

        try:
            compiled_exclude = self._compile_patterns(self.exclude_patterns)
            object.__setattr__(self, "compiled_exclude_patterns", compiled_exclude)
        except ValueError as e:
            raise ValueError(f"Error in exclude_patterns: {e}") from e

        # Setup specific args and pattern specific args
        if self.specific_args is None:
            # Use object.__setattr__ to modify the field even if it's frozen
            object.__setattr__(self, "specific_args", {})

        # Setup pattern specific args
        pattern_specific_args = {}
        if self.specific_args:  # Check if it's not None
            for file_path, v in self.specific_args.items():
                if "patterns" in v:
                    patterns = v.pop("patterns", [])
                    for pattern in patterns:
                        try:
                            compiled_pattern = self._compile_pattern(pattern)
                            pattern_specific_args[compiled_pattern] = v
                        except ValueError as e:
                            raise ValueError(
                                f"Error in specific_args['{file_path}']['patterns']: {e}"
                            ) from e

        object.__setattr__(self, "pattern_specific_args", pattern_specific_args)

        # Setup comparators
        if self.comparators is None:
            object.__setattr__(self, "comparators", get_comparators())

    def _compile_pattern(self, pattern: str) -> Pattern[str]:
        """Compile a regex pattern."""
        try:
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: '{pattern}'") from e

    def _compile_patterns(
        self, patterns: Optional[Iterable[str]]
    ) -> Tuple[Pattern[str], ...]:
        """Compile regex patterns from any iterable to tuple."""
        if patterns is None:
            return ()
        return tuple(self._compile_pattern(pattern) for pattern in patterns)

    # Note: compiled_include_patterns, compiled_exclude_patterns, and pattern_specific_args
    # are now direct attributes set in __attrs_post_init__, no properties needed!

    def should_ignore_file(self, relative_path: str) -> bool:
        """Check if a file should be ignored."""
        # Check inclusion patterns first
        if self.compiled_include_patterns:
            included = any(
                pattern.match(relative_path)
                for pattern in self.compiled_include_patterns
            )
            if not included:
                return True

        # Check exclusion patterns
        return any(
            pattern.match(relative_path) for pattern in self.compiled_exclude_patterns
        )


def compare_files(
    ref_file: str,
    comp_file: str,
    comparator: ComparatorType,
    *args,
    return_raw_diffs: bool = False,
    **kwargs,
) -> Union[bool, str]:
    """Compare 2 files and return the difference.

    Args:
        ref_file: Path to the reference file.
        comp_file: Path to the compared file.
        comparator: The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        return_raw_diffs: If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        *args: passed to the comparator.
        **kwargs: passed to the comparator.

    Returns:
        ``False`` if the files are equal or a string with a message explaining the
        differences if they are different.
    """
    # Get the compared file
    LOGGER.debug("Compare: %s and %s", ref_file, comp_file)

    try:
        return comparator(
            ref_file, comp_file, *args, return_raw_diffs=return_raw_diffs, **kwargs
        )
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
            exception_args = (
                "UNKNOWN ERROR: Could not get information from the exception"
            )
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


def export_formatted_file(
    file: str,
    formatted_file: str,
    comparator: ComparatorType,
    **kwargs,
) -> None:
    """Format a data file and export it.

    .. note:: A new file is created only if the corresponding comparator has saving capability.

    Args:
        file: Path to the compared file.
        formatted_file: Path to the formatted file.
        comparator: The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        **kwargs: Can contain the following dictionaries: 'load_kwargs', 'format_data_kwargs' and
            'save_kwargs'.
    """
    if hasattr(comparator, "save_capability") and comparator.save_capability:
        # pylint: disable=protected-access
        LOGGER.debug("Format: %s into %s", file, formatted_file)
        data = comparator.load(
            file,
            **kwargs.get(
                "load_kwargs",
                (
                    comparator._default_load_kwargs
                    if hasattr(comparator, "_default_load_kwargs")
                    else {}
                ),
            ),
        )
        formatted_data = comparator.format_data(
            data,
            **kwargs.get(
                "format_data_kwargs",
                (
                    comparator._default_format_data_kwargs
                    if hasattr(comparator, "_default_format_data_kwargs")
                    else {}
                ),
            ),
        )
        Path(formatted_file).parent.mkdir(parents=True, exist_ok=True)
        comparator.save(
            formatted_data,
            formatted_file,
            **kwargs.get(
                "save_kwargs",
                (
                    comparator._default_save_kwargs
                    if hasattr(comparator, "_default_save_kwargs")
                    else {}
                ),
            ),
        )
    else:
        LOGGER.debug(
            "Skip formatting for '%s' because the comparator has no saving capability.",
            file,
        )


def pick_comparator(comparator=None, suffix=None, comparators=None):
    """Pick a comparator based on its name or a file suffix."""
    if isinstance(comparator, BaseComparator):
        return comparator
    if comparators is None:
        comparators = get_comparators()
    if comparator is not None:
        for i in comparators.values():  # pragma: no branch
            if i.__class__.__name__ == comparator:
                return i
        LOGGER.debug(
            "Could not find the comparator named '%s' in the given comparators",
            comparator,
        )
    if suffix is not None:
        if suffix in comparators:
            return comparators.get(suffix)
        LOGGER.debug("Could not find the comparator for the '%s' suffix", suffix)
    LOGGER.debug("Returning the default comparator")
    return _COMPARATORS.get(None)


def _check_config(config=None, **kwargs):
    if config is not None:
        if kwargs:
            # Override config attributes with kwargs
            config = attrs.evolve(config, **kwargs)
    else:
        config = ComparisonConfig(
            **kwargs,
        )
    return config


def compare_trees(
    ref_path: Union[str, Path],
    comp_path: Union[str, Path],
    *,
    config: ComparisonConfig = None,
    **kwargs,
):
    """Compare all files from 2 different directory trees and return the differences.

    .. note::

        The comparison only considers the files found in the reference directory. So if there are
        files in the compared directory that do not exist in the reference directory, they are just
        ignored.

    Args:
        ref_path: Path to the reference directory.
        comp_path: Path to the directory that must be compared against the reference.
        config (ComparisonConfig): A config object. If given, all other configuration parameters
            should be set to default values.

    Keyword Args:
        **kwargs (dict): Additional keyword arguments are used to build a ComparisonConfig object
            and will override the values of the given `config` argument.

    Returns:
        dict: A ``dict`` in which the keys are the relative file paths and the values are the
        difference messages. If the directories are considered as equal, an empty ``dict`` is
        returned.
    """
    config = _check_config(config, **kwargs)

    ref_path = Path(ref_path)
    comp_path = Path(comp_path)
    formatted_data_path = comp_path.with_name(
        comp_path.name
        + (
            config.export_formatted_files
            if (
                config.export_formatted_files is not True
                and config.export_formatted_files
            )
            else _DEFAULT_EXPORT_SUFFIX
        )
    )

    # Loop over all files and call the correct comparator
    different_files = {}
    for ref_file in ref_path.glob("**/*"):
        if ref_file.is_dir():
            continue

        relative_path = ref_file.relative_to(ref_path).as_posix()
        comp_file = comp_path / relative_path

        if config.should_ignore_file(relative_path):
            LOGGER.debug("Ignore file: %s", relative_path)
            continue

        if comp_file.exists():
            specific_file_args = (config.specific_args or {}).get(relative_path, None)
            if specific_file_args is None:
                for pattern, pattern_args in config.pattern_specific_args.items():
                    if pattern.match(relative_path):
                        specific_file_args = copy.deepcopy(pattern_args)
                        break
            if specific_file_args is None:
                specific_file_args = {}
            comparator = pick_comparator(
                comparator=specific_file_args.pop("comparator", None),
                suffix=ref_file.suffix,
                comparators=config.comparators,
            )
            comparator_args = specific_file_args.pop("args", [])
            res = compare_files(
                ref_file,
                comp_file,
                comparator,
                *comparator_args,
                return_raw_diffs=config.return_raw_diffs,
                **specific_file_args,
            )
            if res is not False:
                different_files[relative_path] = res
            if config.export_formatted_files is not False:
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

    different_files = compare_trees(
        *args, export_formatted_files=export_formatted_files, **kwargs
    )

    # Sort the files according to their relative paths
    sorted_items = sorted(different_files.items(), key=lambda x: x[0])
    # Test that all files are equal and raise the formatted messages if there are differences
    if len(sorted_items) > 0:
        raise AssertionError("\n\n\n".join([i[1] for i in sorted_items]))

    # Return True if the trees are equal
    return True

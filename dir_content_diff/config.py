"""Configuration classes for directory content comparison.

This module contains the configuration classes and validation functions.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import re
from collections.abc import Callable
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Literal
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import Union

import attrs

from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.registry import get_comparators

# Type alias for comparators
ComparatorType = Union[BaseComparator, Callable]


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
        max_workers: Maximum number of worker threads/processes for parallel execution. If None,
            defaults to min(32, (os.cpu_count() or 1) + 4) as per executor default.
        executor_type: Type of executor to use for parallel execution. 'thread' uses
            ThreadPoolExecutor (better for I/O-bound tasks), 'process' uses ProcessPoolExecutor
            (better for CPU-bound tasks), 'sequential' disables parallel execution.
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
    executor_type: Literal["sequential", "thread", "process"] = attrs.field(
        default="sequential"
    )
    max_workers: Optional[int] = attrs.field(default=None)

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

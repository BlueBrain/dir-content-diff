"""Extension module to process files with Pandas."""
try:
    import pandas as pd
except ImportError as exception:  # pragma: no cover
    raise ImportError("Could not import pandas package, please install it.") from exception

from dir_content_diff import register_comparator
from dir_content_diff.base_comparators import BaseComparator


class DataframeComparator(BaseComparator):
    """Comparator for :class:`pandas.DataFrame` objects."""

    def format_data(self, data, ref=None, replace_pattern=None):
        """Format the compared :class:`pandas.DataFrame`.

        Args:
            data (pandas.DataFrame): The DataFrame to format.
            ref (pandas.DataFrame): (Optional) The reference DataFrame.
            **replace_pattern (dict): (Optional) The columns that contain a given pattern which
                must be made replaced.
                The dictionary must have the following format:

                .. code-block:: python

                    {
                        (<pattern>, <new_value>, <optional regex flag>): [col1, col2]
                    }

        .. note::
            The formatting errors are stored in `self.current_state["format_errors"]`.
            It contains a dict in which the keys are the columns with detected issues and the
            values are the actual descriptions of these issues.

        Returns:
            pandas.DataFrame: The formatted compared data.
        """
        self.current_state["format_errors"] = errors = {}

        if replace_pattern is not None:
            for pat, cols in replace_pattern.items():
                pattern = pat[0]
                new_value = pat[1]
                if len(pat) > 2:
                    flags = pat[2]
                else:
                    flags = 0
                for col in cols:
                    if ref is not None and col not in ref.columns:
                        errors[col] = (
                            "The column is missing in the reference DataFrame, please fix the "
                            "'replace_pattern' argument."
                        )
                    elif col not in data.columns:
                        errors[col] = (
                            "The column is missing in the compared DataFrame, please fix the "
                            "'replace_pattern' argument."
                        )
                    elif hasattr(data[col], "str"):
                        # If all values are NaN, Pandas casts the column dtype to float, so the str
                        # attribute is not available.
                        data[col] = data[col].str.replace(
                            pattern,
                            new_value,
                            flags=flags,
                            regex=True,
                        )

        return data

    def diff(self, ref, comp, *args, ignore_columns=None, **kwargs):
        """Compare two :class:`pandas.DataFrame` objects.

        This function calls :func:`pandas.testing.assert_series_equal`, read the doc of this
        function for details on args and kwargs.

        Args:
            ref (pandas.DataFrame): The reference DataFrame.
            comp (pandas.DataFrame): The compared DataFrame.
            **ignore_columns (list(str)): (Optional) The columns that should not be checked.

        Returns:
            bool or str: ``False`` if the DataFrames are considered as equal or a string explaining
            why they are not considered equal.
        """
        errors = self.current_state.get("format_errors", {})

        if ignore_columns is not None:
            ref.drop(columns=ignore_columns, inplace=True, errors="ignore")
            comp.drop(columns=ignore_columns, inplace=True, errors="ignore")

        for col in ref.columns:
            if col in errors:
                continue
            try:
                if col not in comp.columns:
                    errors[col] = "The column is missing in the compared DataFrame."
                else:
                    pd.testing.assert_series_equal(ref[col], comp[col], *args, **kwargs)
                    errors[col] = True
            except AssertionError as e:
                errors[col] = e.args[0]

        for col in comp.columns:
            if col not in errors and col not in ref.columns:
                errors[col] = "The column is missing in the reference DataFrame."

        not_equals = {k: v for k, v in errors.items() if v is not True}
        if len(not_equals) == 0:
            return False
        return not_equals

    def format_diff(self, difference):
        """Format one element difference."""
        k, v = difference
        return f"\nColumn '{k}': {v}"

    def sort(self, differences):
        """Do not sort the differences to keep the column order."""
        return differences


class CsvComparator(DataframeComparator):
    """Comparator for CSV files."""

    def load(self, path, **kwargs):
        """Load a CSV file into a :class:`pandas.DataFrame` object."""
        return pd.read_csv(path, **kwargs)

    def save(self, data, path, **kwargs):
        """Save data to a CSV file."""
        index = kwargs.pop("index", False)
        data.to_csv(path, index=index, **kwargs)


class HdfComparator(DataframeComparator):
    """Comparator for HDF files."""

    def load(self, path, **kwargs):
        """Load a HDF file into a :class:`pandas.DataFrame` object."""
        return pd.read_hdf(path, **kwargs)

    def save(self, data, path, **kwargs):
        """Save data to a HDF file."""
        index = kwargs.pop("index", False)
        key = kwargs.pop("key", "data")
        data.to_hdf(path, index=index, key=key, **kwargs)


def register():
    """Register Pandas extensions."""
    register_comparator(".csv", CsvComparator())
    register_comparator(".tsv", CsvComparator())
    register_comparator(".h4", HdfComparator())
    register_comparator(".h5", HdfComparator())
    register_comparator(".hdf", HdfComparator())
    register_comparator(".hdf4", HdfComparator())
    register_comparator(".hdf5", HdfComparator())

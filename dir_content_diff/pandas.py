"""Extension module to process files with Pandas."""
try:
    import pandas as pd
except ImportError as exception:  # pragma: no cover
    raise ImportError("Could not import pandas package, please install it.") from exception

from dir_content_diff import register_comparator
from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.util import diff_msg_formatter


def format_dataframe(comp, replace_pattern=None, ref=None):
    """Format the compared :class:`pandas.DataFrame`.

    Returns:
        A dict in which the keys are the columns with detected issues and the values are the
        actual descriptions of these issues.
    """
    res = {}

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
                    res[col] = (
                        "The column is missing in the reference DataFrame, please fix the "
                        "'replace_pattern' argument."
                    )
                elif col not in comp.columns:
                    res[col] = (
                        "The column is missing in the compared DataFrame, please fix the "
                        "'replace_pattern' argument."
                    )
                elif hasattr(comp[col], "str"):
                    # If all values are NaN, Pandas casts the column dtype to float, so the str
                    # attribute is not available.
                    comp[col] = comp[col].str.replace(pattern, new_value, flags=flags, regex=True)

    return res


class DataframeComparator(BaseComparator):
    """Comparator for :class:`pandas.DataFrame` objects."""

    def diff(self, ref, comp, *args, **kwargs):
        """Compare two :class:`pandas.DataFrame` objects.

        This function calls :func:`pandas.testing.assert_series_equal`, read the doc of this
        function for details on args and kwargs.

        Args:
            ref (pandas.DataFrame): The reference DataFrame.
            comp (pandas.DataFrame): The compared DataFrame.
            **ignore_columns (list(str)): (Optional) The columns that should not be checked.
            **replace_pattern (dict): (Optional) The columns that contain a given pattern which
                must be made replaced.
                The dictionary must have the following format:

                .. code-block:: python

                    {
                        (<pattern>, <new_value>, <optional regex flag>): [col1, col2]
                    }

        Returns:
            bool or str: ``False`` if the DataFrames are considered as equal or a string explaining
            why they are not considered equal.
        """
        ignore_columns = kwargs.pop("ignore_columns", None)
        replace_pattern = kwargs.pop("replace_pattern", None)

        res = format_dataframe(comp, replace_pattern, ref=ref)

        if ignore_columns is not None:
            ref.drop(columns=ignore_columns, inplace=True, errors="ignore")
            comp.drop(columns=ignore_columns, inplace=True, errors="ignore")

        for col in ref.columns:
            if col in res:
                continue
            try:
                if col not in comp.columns:
                    res[col] = "The column is missing in the compared DataFrame."
                else:
                    pd.testing.assert_series_equal(ref[col], comp[col], *args, **kwargs)
                    res[col] = True
            except AssertionError as e:
                res[col] = e.args[0]

        for col in comp.columns:
            if col not in res and col not in ref.columns:
                res[col] = "The column is missing in the reference DataFrame."

        not_equals = {k: v for k, v in res.items() if v is not True}
        if len(not_equals) == 0:
            return False
        return not_equals

    def format(self, difference):
        """Format one element difference."""
        k, v = difference
        return f"\nColumn '{k}': {v}"

    def sort(self, differences):
        """Do not sort the differences to keep the column order."""
        return differences

    def report(self, ref_file, comp_file, formatted_differences, diff_args, diff_kwargs):
        """Create a report from the formatted differences."""
        # if not isinstance(formatted_differences, bool):
        #     formatted_differences = "\n".join(formatted_differences)
        return diff_msg_formatter(
            ref_file,
            comp_file,
            formatted_differences,
            diff_args,
            diff_kwargs,
        )


class CsvComparator(DataframeComparator):
    """Comparator for CSV files."""

    def load(self, path, **kwargs):
        """Load a CSV file into a :class:`pandas.DataFrame` object."""
        return pd.read_csv(path, **kwargs)


def save_csv_file(
    file_path,
    file_dest,
    replace_pattern=None,
    read_csv_kwargs=None,
    ref_path=None,
    **to_csv_kwargs,
):
    """Format and export data from a CSV / TSV / DAT file.

    Args:
        file_path (str): The path to the CSV file.
        file_dest (str): The path to the CSV file in which the formatted data will be exported.
        replace_pattern (list(str)): See :class:`DataframeComparator`.
        read_csv_kwargs (dict): The kwargs that should be passed to :func:`pandas.read_csv`.
        ref_path (str): The path to the reference CSV file if the formatting function needs it.
        to_csv_kwargs (dict): The kwargs that should be passed to :meth:`pandas.DataFrame.to_csv`.

    Returns:
        See :func:`format_dataframe`.
    """
    if read_csv_kwargs is None:
        read_csv_kwargs = {}
    comp = pd.read_csv(file_path, **read_csv_kwargs)

    if ref_path is not None:
        ref = pd.read_csv(ref_path, **read_csv_kwargs)
    else:
        ref = None
    res = format_dataframe(comp, replace_pattern, ref=ref)

    comp.to_csv(file_dest, **to_csv_kwargs)

    return res


def register_pandas():
    """Register Pandas extensions."""
    register_comparator(".csv", CsvComparator())
    register_comparator(".tsv", CsvComparator())

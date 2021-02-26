"""Extension module to process files with Pandas."""
try:
    import pandas as pd
except ImportError as exception:  # pragma: no cover
    raise ImportError("Could not import pandas package, please install it.") from exception

from dir_content_diff import register_comparator
from dir_content_diff.util import diff_msg_formatter


def compare_dataframes(ref, comp, *args, ignore_columns=None, replace_pattern=None, **kwargs):
    """Compare two :class:`Pandas.DataFrames`.

    This function calls :func:`pandas.testing.assert_series_equal`, read the doc of this function
    for details on args and kwargs.

    Args:
        ref (pandas.DataFrame): The reference DataFrame.
        comp (pandas.DataFrame): The compared DataFrame.
        ignore_columns (list): The columns that should not be checked.
        replace_pattern (dict): The columns that contain a given pattern which must be made
            replaced. The dictionary must be as the following:

            .. code-block:: python

                {
                    (<pattern>, <new_value>, <optional regex flag>): [col1, col2]
                }

    Returns:
        bool or str: ``True`` if the DataFrames are considered as equal or a string explaining why
        they are not considered as equal.
    """
    if ignore_columns is not None:
        ref.drop(columns=ignore_columns, inplace=True, errors="ignore")
        comp.drop(columns=ignore_columns, inplace=True, errors="ignore")

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
                if col not in ref.columns:
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
                    comp[col] = comp[col].str.replace(pattern, new_value, flags=flags)

    for col in ref.columns:
        if col in res:
            continue
        try:
            if col not in comp.columns:
                res[col] = "The column is missing in the compared DataFrame."
            else:
                pd.testing.assert_series_equal(ref[col], comp[col], *args, **kwargs)
                res[col] = True
        except AssertionError as exception:
            res[col] = exception.args[0]

    for col in comp.columns:
        if col not in res and col not in ref.columns:
            res[col] = "The column is missing in the reference DataFrame."

    not_equals = {k: v for k, v in res.items() if v is not True}
    if len(not_equals) == 0:
        return True
    return "\n".join([f"\nColumn '{k}': {v}" for k, v in not_equals.items()])


def compare_csv_files(
    ref_path,
    comp_path,
    *args,
    ignore_columns=None,
    replace_pattern=None,
    read_csv_kwargs=None,
    **kwargs,
):
    """Compare data from two CSV / TSV / DAT files.

    This function calls :func:`compare_dataframes`, read the doc of this function for details on
    args and kwargs.

    Args:
        ref_path (str): The path to the reference CSV file.
        comp_path (str): The path to the compared CSV file.
        read_csv_kwargs (dict): The kwargs that should be passed to :func:`pandas.read_csv`.

    Returns:
        bool or str: ``True`` if the DataFrames are considered as equal or a string explaining why
        they are not considered as equal.
    """
    if read_csv_kwargs is None:
        read_csv_kwargs = {}
    ref = pd.read_csv(ref_path, **read_csv_kwargs)
    comp = pd.read_csv(comp_path, **read_csv_kwargs)

    res = compare_dataframes(
        ref,
        comp,
        *args,
        ignore_columns=ignore_columns,
        replace_pattern=replace_pattern,
        **kwargs,
    )

    return diff_msg_formatter(ref_path, comp_path, res, args, kwargs)


def register_pandas():
    """Register Pandas extensions."""
    register_comparator(".csv", compare_csv_files)
    register_comparator(".tsv", compare_csv_files)

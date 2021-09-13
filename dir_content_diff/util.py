"""Some utils used by the ``dir-content-diff`` package."""
import re

_ext_pattern = re.compile(r"\.?(.*)")


def format_ext(ext):
    """Ensure that the given extension string begins with a dot.

    Args:
        ext(str): The extension to format.

    Returns:
        The formatted extension.
    """
    match = re.match(_ext_pattern, ext)
    return f".{match.group(1)}"


def diff_msg_formatter(
    ref,
    comp,
    reason=None,
    diff_args=None,
    diff_kwargs=None,
    load_kwargs=None,
    format_data_kwargs=None,
    filter_kwargs=None,
    format_diff_kwargs=None,
    sort_kwargs=None,
    concat_kwargs=None,
    report_kwargs=None,
):  # pylint: disable=too-many-arguments
    """Format a difference message.

    Args:
        ref (str): The path to the reference file.
        comp (str): The path to the compared file.
        reason (bool or str): If the reason is False, False is returned. If it is a str, a formatted
            message is returned.
        diff_args (list): (optional) The args used for the comparison.
        diff_kwargs (list): (optional) The kwargs used for the comparison.
        load_kwargs (dict): The kwargs used for loading the data.
        format_data_kwargs (dict): The kwargs used for formatting the data.
        filter_kwargs (dict): The kwargs used for filtering the differences.
        format_diff_kwargs (dict): The kwargs used for formatting the differences.
        sort_kwargs (dict): The kwargs used for sorting the differences.
        concat_kwargs (dict): The kwargs used for concatenating the differences.
        report_kwargs (dict): The kwargs used for reporting the differences.

    Returns:
        False or the difference message.
    """
    if not reason:
        return False

    if reason is not None and reason is not True:
        reason_used = f"{reason}"
    else:
        reason_used = ""

    if diff_args:
        args_used = f"Args used for computing differences: {list(diff_args)}\n"
    else:
        args_used = ""

    def format_kwargs(kwargs, name):
        if kwargs:
            return f"Kwargs used for {name}: {kwargs}\n"
        return ""

    diff_kwargs_used = format_kwargs(diff_kwargs, "computing differences")
    load_kwargs_used = format_kwargs(load_kwargs, "loading data")
    format_data_kwargs_used = format_kwargs(format_data_kwargs, "formatting data")
    filter_kwargs_used = format_kwargs(filter_kwargs, "filtering differences")
    format_diff_kwargs_used = format_kwargs(format_diff_kwargs, "formatting differences")
    sort_kwargs_used = format_kwargs(sort_kwargs, "sorting differences")
    concat_kwargs_used = format_kwargs(concat_kwargs, "concatenating differences")
    report_kwargs_used = format_kwargs(report_kwargs, "reporting differences")

    kwargs_used = "\n".join(
        i
        for i in [
            load_kwargs_used,
            format_data_kwargs_used,
            diff_kwargs_used,
            filter_kwargs_used,
            format_diff_kwargs_used,
            sort_kwargs_used,
            concat_kwargs_used,
            report_kwargs_used,
        ]
        if i
    )

    eol = "."
    if reason_used or args_used or kwargs_used:
        eol = ":\n"

    return (
        f"The files '{ref}' and '{comp}' are different{eol}"
        f"{args_used}"
        f"{kwargs_used}"
        f"{reason_used}"
    )

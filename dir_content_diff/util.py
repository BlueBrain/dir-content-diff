"""Some utils used by the dir-content-diff package."""
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


def diff_msg_formatter(ref, comp, reason=None, args=None, kwargs=None):
    """Format a diff message.

    Args:
        ref (str): The path to the reference file.
        comp (str): The path to the compared file.
        reason (bool or str): If the reason is True, True is returned. If it is a str, a formatted
            message is returned.
        args (list): (optional) The args used for the comparison.
        kwargs (list): (optional) The kwargs used for the comparison.

    Returns:
        True or the diff message.
    """
    if reason is True:
        return True

    if reason is not None and reason is not False:
        reason_used = f"{reason}"
    else:
        reason_used = ""

    if args:
        args_used = f"Args used: {list(args)}\n"
    else:
        args_used = ""

    if kwargs:
        kwargs_used = f"Kwargs used: {kwargs}\n"
    else:
        kwargs_used = ""

    eol = "."
    if reason_used or args_used or kwargs_used:
        eol = ":\n"

    return (
        f"The files '{ref}' and '{comp}' are different{eol}"
        f"{args_used}"
        f"{kwargs_used}"
        f"{reason_used}"
    )

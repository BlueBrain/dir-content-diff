"""Main entry point of the Command Line Interface for the dir-content-diff package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import json
import logging
import sys
from pathlib import Path
from typing import Optional
from typing import Union

import click
from yaml import safe_load

from dir_content_diff import compare_files
from dir_content_diff import compare_trees
from dir_content_diff import export_formatted_file
from dir_content_diff import pick_comparator
from dir_content_diff.core import _DEFAULT_EXPORT_SUFFIX
from dir_content_diff.util import LOGGER


def setup_logger(level: str = "info"):
    """Setup application logger."""
    level = level.lower()
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    logging.basicConfig(
        format="%(levelname)s - %(message)s",
        # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        # datefmt="%Y-%m-%dT%H:%M:%S",
        level=levels[level],
    )


def load_config(ctx, param, value):  # pylint: disable=unused-argument
    """Load configuration from the given path."""
    # pylint: disable=raise-missing-from
    ctx.config = {}
    if value is not None:
        try:
            ctx.config = json.loads(value)
        except Exception:  # pylint: disable=broad-exception-caught
            path = Path(value)
            if not path.exists():
                msg = f"The file '{path}' does not exist."
                raise FileNotFoundError(msg)
            try:
                with path.open(encoding="utf-8") as f:
                    ctx.config = safe_load(f.read())
            except Exception:  # pylint: disable=broad-exception-caught
                msg = (
                    "Could not load the configuration because it could not be parsed as a JSON "
                    "string nor as a YAML file."
                )
                raise SyntaxError(msg) from None


@click.command(
    short_help="Compare the two given inputs",
    epilog=(
        "Note: When comparing directories, only the files located in the REFERENCE_INPUT will be "
        "considered in the COMPARED_INPUT."
    ),
)
@click.argument("reference_input", type=click.Path(dir_okay=True, exists=True))
@click.argument("compared_input", type=click.Path(dir_okay=True, exists=True))
@click.option(
    "-c",
    "--config",
    callback=load_config,
    is_eager=True,
    expose_value=False,
    show_default=True,
    help="Read option defaults from the given JSON string or the specified YAML file.",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="The logger level.",
)
@click.option(
    "-f/-nf",
    "--export-formatted-files/--no-export-formatted-files",
    default=False,
    help="Export the files after they were formatted by the comparators.",
)
@click.option(
    "-s/-ns",
    "--sort-diffs/--no-sort-diffs",
    default=False,
    help="Sort the differences by file name.",
)
@click.option(
    "--executor-type",
    type=click.Choice(["sequential", "thread", "process"]),
    default="sequential",
    help="Type of executor for execution. 'sequential' for single-threaded, "
    "'thread' for I/O-bound tasks, 'process' for CPU-bound tasks.",
)
@click.option(
    "--max-workers",
    type=int,
    help="Maximum number of worker threads/processes for parallel execution. "
    "Only used with 'thread' or 'process' executor types.",
)
@click.version_option()
@click.pass_context
def main(ctx, *args, **kwargs):
    """A command line tool for directory or file comparison.

    REFERENCE_INPUT is the file or directory considered as the reference for comparison.

    COMPARED_INPUT is the file or directory considered as the compared input.
    """
    log_level = kwargs.pop("log_level", "info")

    setup_logger(log_level)

    LOGGER.debug("Running the following command: %s", " ".join(sys.argv))
    LOGGER.debug("Running from the following folder: %s", Path.cwd())

    ref = Path(kwargs.pop("reference_input"))
    comp = Path(kwargs.pop("compared_input"))

    # Extract execution options
    executor_type = kwargs.pop("executor_type", "sequential")
    max_workers = kwargs.pop("max_workers", None)

    input_diff(
        ref,
        comp,
        ctx.config,
        kwargs.pop("export_formatted_files", False),
        kwargs.pop("sort_diffs", False),
        executor_type,
        max_workers,
    )


def input_diff(
    ref: Union[str, Path],
    comp: Union[str, Path],
    config,
    export_formatted_files: Union[bool, str] = False,
    sort_diffs: bool = False,
    executor_type: str = "sequential",
    max_workers: Optional[int] = None,
):
    """Compute and display differences from given inputs."""
    ref = Path(ref)
    comp = Path(comp)
    ref_is_dir = ref.is_dir()
    comp_is_dir = comp.is_dir()
    if ref_is_dir != comp_is_dir:
        msg = "The reference and compared inputs must both be either two directories or two files."
        raise ValueError(msg)

    if ref_is_dir:
        res = compare_trees(
            ref,
            comp,
            specific_args=config,
            export_formatted_files=export_formatted_files,
            executor_type=executor_type,
            max_workers=max_workers,
        )
    else:
        comparator_name = config.pop("comparator", None)
        comparator = pick_comparator(
            comparator=comparator_name,
            suffix=ref.suffix,
        )
        diff = compare_files(ref, comp, comparator, **config)
        res = {str(ref): diff} if diff is not False else {}
        if export_formatted_files:
            export_formatted_file(
                ref,
                ref.with_name(ref.stem + _DEFAULT_EXPORT_SUFFIX).with_suffix(
                    ref.suffix
                ),
                comparator,
                **config,
            )
            export_formatted_file(
                comp,
                comp.with_name(comp.stem + _DEFAULT_EXPORT_SUFFIX).with_suffix(
                    comp.suffix
                ),
                comparator,
                **config,
            )

    if res:
        if sort_diffs:
            res_list = sorted(res.items(), key=lambda x: x[0])
        else:
            res_list = res.items()

        LOGGER.info(
            "Differences found between '%s' and '%s':\n\n\n%s",
            ref,
            comp,
            ("\n\n\n".join([i[1] for i in res_list])),
        )
    else:
        LOGGER.info("No difference found between '%s' and '%s'", ref, comp)

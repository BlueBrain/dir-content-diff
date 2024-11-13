"""Main entry point of the Command Line Interface for the dir-content-diff package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2024 Blue Brain Project, EPFL.
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

import click
from yaml import safe_load

from dir_content_diff import compare_files
from dir_content_diff import compare_trees
from dir_content_diff import export_formatted_file
from dir_content_diff import pick_comparator
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


def load_config(ctx, param, value):
    """Load configuration from the given path."""
    ctx.config = {}
    if value is not None:
        try:
            ctx.config = json.loads(value)
        except Exception as json_exc:
            try:
                path = Path(value)
                if not path.exists():
                    msg = f"The file '{path}' does not exist."
                    raise FileNotFoundError(msg)
                with path.open() as f:
                    ctx.config = safe_load(f.read())
            except Exception as path_exc:
                raise path_exc from json_exc


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
    input_diff(
        ref,
        comp,
        ctx.config,
        kwargs.pop("export_formatted_files", False),
        kwargs.pop("sort_diffs", False),
    )


def input_diff(ref, comp, config, export_formatted_files=False, sort_diffs=False):
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
        )
        if sort_diffs:
            res = sorted(res.items(), key=lambda x: x[0])
    else:
        comparator_name = config.pop("comparator", None)
        comparator = pick_comparator(
            comparator=comparator_name,
            suffix=ref.suffix,
        )
        res = {str(ref): compare_files(ref, comp, comparator, **config)}
        if export_formatted_files:
            export_formatted_file(ref, **config)
            export_formatted_file(comp, **config)

    if res:
        LOGGER.info(
            "Differences found between '%s' and '%s':\n\n\n%s",
            ref,
            comp,
            ("\n\n\n".join([i[1] for i in res.items()])),
        )
    else:
        LOGGER.info("No difference found between '%s' and '%s'", ref, comp)

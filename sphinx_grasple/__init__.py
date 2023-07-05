# -*- coding: utf-8 -*-
"""
sphinx_grasple
~~~~~~~~~~~~~~~
This package is an extension for sphinx to support Grasple exercises embedded in
an iframe.
This project is a fork of the sphinx-exercise package by the Executable Books team, 
see AUTHORS in the original project (Copyright 2020-2021 by Executable Books).
:copyright: Dani Balagué Guardia
:license: MIT, see LICENSE for details.
"""

from pathlib import Path
from typing import Any, Dict, Set, Union, cast
from sphinx.config import Config
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.domains.std import StandardDomain
from docutils.nodes import Node
from sphinx.util import logging
from sphinx.util.fileutil import copy_asset

from .directive import (
    GraspleExerciseDirective,
)

from .nodes import (
    grasple_exercise_node,
    grasple_exercise_enumerable_node,
    visit_grasple_exercise_node,
    depart_grasple_exercise_node,
    visit_grasple_exercise_enumerable_node,
    depart_grasple_exercise_enumerable_node,
    grasple_exercise_end_node,
    is_extension_node,
    grasple_exercise_title,
    grasple_exercise_subtitle,
    exercise_latex_number_reference,
    visit_exercise_latex_number_reference,
    depart_exercise_latex_number_reference,
)

from .post_transforms import (
    ResolveTitlesInGraspleExercises,
    UpdateReferencesToGraspleEnumerated,
)

logger = logging.getLogger(__name__)


# Callback Functions


def purge_grasple_exercises(app: Sphinx, env: BuildEnvironment, docname: str) -> None:
    """Purge sphinx_grasple_exercise registry"""

    if not hasattr(env, "sphinx_grasple_exercise_registry"):
        return

    # Purge env.sphinx_grasple_exercise_registry if matching docname
    remove_labels = [
        label
        for (label, node) in env.sphinx_grasple_exercise_registry.items()
        if node["docname"] == docname
    ]
    if remove_labels:
        for label in remove_labels:
            del env.sphinx_grasple_exercise_registry[label]


def merge_exercises(
    app: Sphinx, env: BuildEnvironment, docnames: Set[str], other: BuildEnvironment
) -> None:
    """Merge sphinx_grasple_exercise_registry"""

    if not hasattr(env, "sphinx_grasple_exercise_registry"):
        env.sphinx_exercise_registry = {}

    # Merge env stored data
    if hasattr(other, "sphinx_grasple_exercise_registry"):
        env.sphinx_exercise_registry = {
            **env.sphinx_grasple_exercise_registry,
            **other.sphinx_grasple_exercise_registry,
        }


def init_numfig(app: Sphinx, config: Config) -> None:
    """Initialize numfig"""

    config["numfig"] = True
    numfig_format = {"grasple-exercise": "Grasple Exercise %s"}
    # Merge with current sphinx settings
    numfig_format.update(config.numfig_format)
    config.numfig_format = numfig_format


def copy_asset_files(app: Sphinx, exc: Union[bool, Exception]):
    """Copies required assets for formating in HTML"""

    static_path = (
        Path(__file__).parent.joinpath("assets", "html", "grasple-exercise.css").absolute()
    )
    asset_files = [str(static_path)]

    if exc is None:
        for path in asset_files:
            copy_asset(path, str(Path(app.outdir).joinpath("_static").absolute()))


def doctree_read(app: Sphinx, document: Node) -> None:
    """
    Read the doctree and apply updates to sphinx-grasple nodes
    """

    domain = cast(StandardDomain, app.env.get_domain("std"))

    # Traverse sphinx-exercise nodes
    for node in document.traverse():
        if is_extension_node(node):
            name = node.get("names", [])[0]
            label = document.nameids[name]
            docname = app.env.docname
            section_name = node.attributes.get("title")
            domain.anonlabels[name] = docname, label
            domain.labels[name] = docname, label, section_name


def setup(app: Sphinx) -> Dict[str, Any]:

    app.connect("config-inited", init_numfig)  # event order - 1
    app.connect("env-purge-doc", purge_grasple_exercises)  # event order - 5 per file
    app.connect("doctree-read", doctree_read)  # event order - 8
    app.connect("env-merge-info", merge_exercises)  # event order - 9
    app.connect("build-finished", copy_asset_files)  # event order - 16

    app.add_node(
        grasple_exercise_node,
        singlehtml=(visit_grasple_exercise_node, depart_grasple_exercise_node),
        html=(visit_grasple_exercise_node, depart_grasple_exercise_node),
        latex=(visit_grasple_exercise_node, depart_grasple_exercise_node),
    )

    app.add_enumerable_node(
        grasple_exercise_enumerable_node,
        "grasple-exercise",
        None,
        singlehtml=(visit_grasple_exercise_enumerable_node, depart_grasple_exercise_enumerable_node),
        html=(visit_grasple_exercise_enumerable_node, depart_grasple_exercise_enumerable_node),
        latex=(visit_grasple_exercise_enumerable_node, depart_grasple_exercise_enumerable_node),
    )

    # Internal Title Nodes that don't need visit_ and depart_ methods
    # as they are resolved in post_transforms to docutil and sphinx nodes
    app.add_node(grasple_exercise_end_node)
    app.add_node(grasple_exercise_title)
    app.add_node(grasple_exercise_subtitle)

    app.add_node(
        exercise_latex_number_reference,
        latex=(
            visit_exercise_latex_number_reference,
            depart_exercise_latex_number_reference,
        ),
    )

    app.add_directive("grasple", GraspleExerciseDirective)

    app.add_post_transform(UpdateReferencesToGraspleEnumerated)
    app.add_post_transform(ResolveTitlesInGraspleExercises)

    app.add_css_file("grasple-exercise.css")

    return {
        "version": "builtin",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

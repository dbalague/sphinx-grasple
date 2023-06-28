"""
sphinx_exercise.directive
~~~~~~~~~~~~~~~~~~~~~~~~~

A custom Sphinx Directive for Grasple Exercises
This file is modified from the original sphinx_exercise
(Copyright 2020 by the QuantEcon team, see AUTHORS in 
the original project)
:copyright: Dani Balagué Guardia
:licences: see LICENSE for details
:modifications: changed the directive to add an iframe
                and a description of the exercise
"""

from typing import List
from docutils.nodes import Node

from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from .nodes import (
    grasple_exercise_node,
    grasple_exercise_enumerable_node,
    grasple_exercise_end_node,
    grasple_exercise_title,
    grasple_exercise_subtitle
)
from docutils import nodes
from sphinx.util import logging

logger = logging.getLogger(__name__)


class SphinxGraspleExerciseBaseDirective(SphinxDirective):
    def duplicate_labels(self, label):
        """Check for duplicate labels"""

        if not label == "" and label in self.env.sphinx_grasple_exercise_registry.keys():
            docpath = self.env.doc2path(self.env.docname)
            path = docpath[: docpath.rfind(".")]
            other_path = self.env.doc2path(
                self.env.sphinx_exercise_registry[label]["docname"]
            )
            msg = f"duplicate label: {label}; other instance in {other_path}"
            logger.warning(msg, location=path, color="red")
            return True

        return False


class GraspleExerciseDirective(SphinxGraspleExerciseBaseDirective):
    """
    An exercise directive

    .. exercise:: <subtitle> (optional)
       :label:
       :class:
       :nonumber:
       :hidden:
       :url:

    Arguments
    ---------
    subtitle : str (optional)
            Specify a custom subtitle to add to the exercise output

    Parameters:
    -----------
    label : str,
            A unique identifier for your exercise that you can use to reference
            it with {ref} and {numref}
    class : str,
            Value of the exercise’s class attribute which can be used to add custom CSS
    nonumber :  boolean (flag),
                Turns off exercise auto numbering.
    hidden  :   boolean (flag),
                Removes the directive from the final output.
    url : str,
            Grasple exercise URL
    """

    name = "grasple-exercise"
    has_content = False
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "label": directives.unchanged_required,
        "class": directives.class_option,
        "nonumber": directives.flag,
        "hidden": directives.flag,
        "url" : directives.unchanged,
        "description" : directives.unchanged,
        "iframe_width": directives.unchanged,
        "iframe_height": directives.unchanged,
        "dropdown" : directives.flag
    }

    def run(self) -> List[Node]:

        # Parse options
        description = self.options.get('description')
        url = self.options.get('url')
        iframe_width = self.options.get('iframe_width', '100%')
        iframe_height = self.options.get('iframe_height', '400px')
        dropdown = 'dropdown' in self.options

        self.defaults = {"title_text": "Grasple Exercise"}
        self.serial_number = self.env.new_serialno()

        # Initialise Registry (if needed)
        if not hasattr(self.env, "sphinx_grasple_exercise_registry"):
            self.env.sphinx_grasple_exercise_registry = {}

        # Construct Title
        title = grasple_exercise_title()
        title += nodes.Text(self.defaults["title_text"])

        # Select Node Type and Initialise
        if "nonumber" in self.options:
            node = grasple_exercise_node()
        else:
            node = grasple_exercise_enumerable_node()

        if self.name == "grasple-exercise-start":
            node.gated = True

        # Parse custom subtitle option
        if self.arguments != []:
            subtitle = grasple_exercise_subtitle()
            subtitle_text = f"{self.arguments[0]}"
            subtitle_nodes, _ = self.state.inline_text(subtitle_text, self.lineno)
            for subtitle_node in subtitle_nodes:
                subtitle += subtitle_node
            title += subtitle

        # State Parsing
        section = nodes.section(ids=["admonition-content"])

        # Add the description if provided
        if description:
            description_container = nodes.container(classes=['description'])
            self.state.nested_parse(self.content, self.content_offset, description_container)
            section += description_container.children

        # Create the iframe HTML code
        iframe_html = f'<iframe src="{url}" width="{iframe_width}" height="{iframe_height}"></iframe>'
        iframe_node = nodes.raw('', iframe_html, format='html')

        if dropdown:
            # Wrap the iframe in a dropdown container if the dropdown option is specified
            dropdown_content = nodes.container(classes=['dropdown-content'])
            dropdown_content += iframe_node

            # Wrap the dropdown content in a container with CSS classes for styling
            container_node = nodes.container(classes=['dropdown-container'])
            container_node += dropdown_content

            # Create the details element with the summary and container
            details_html = '<details class="dropdown"><summary>Show/Hide Content</summary>{}</details>'.format(container_node.astext())
            details_node = nodes.raw('', details_html, format='html')

            # Add the details element to the exercise node
            section += details_node
        else:
            # Add the iframe directly to the exercise node
            section += iframe_node

        # Construct a label
        label = self.options.get("label", "")
        if label:
            # TODO: Check how :noindex: is used here
            self.options["noindex"] = False
        else:
            self.options["noindex"] = True
            label = f"{self.env.docname}-grasple-exercise-{self.serial_number}"

        # Check for Duplicate Labels
        # TODO: Should we just issue a warning rather than skip content?
        if self.duplicate_labels(label):
            return []

        # Collect Classes
        classes = [f"{self.name}"]
        if self.options.get("class"):
            classes.extend(self.options.get("class"))

        self.options["name"] = label

        # Construct Node
        node += title
        node += section
        node["classes"].extend(classes)
        node["ids"].append(label)
        node["label"] = label
        node["docname"] = self.env.docname
        node["title"] = self.defaults["title_text"]
        node["type"] = self.name
        node["hidden"] = True if "hidden" in self.options else False
        node["serial_number"] = self.serial_number
        node.document = self.state.document

        self.add_name(node)
        self.env.sphinx_grasple_exercise_registry[label] = {
            "type": self.name,
            "docname": self.env.docname,
            "node": node,
        }

        # TODO: Could tag this as Hidden to prevent the cell showing
        # rather than removing content
        # https://github.com/executablebooks/sphinx-jupyterbook-latex/blob/8401a27417d8c2dadf0365635bd79d89fdb86550/sphinx_jupyterbook_latex/transforms.py#L108
        if node.get("hidden", bool):
            return []

        return [node]

# Gated Directives

class GraspleExerciseStartDirective(GraspleExerciseDirective):
    """
    A gated directive for exercises

    .. exercise:: <subtitle> (optional)
       :label:
       :class:
       :nonumber:
       :hidden:
       :url:

    This class is a child of GraspleExerciseDirective so it supports
    all the same options as the base exercise node
    """

    name = "grasple-exercise-start"

    def run(self):
        # Initialise Gated Registry
        if not hasattr(self.env, "sphinx_grasple_exercise_gated_registry"):
            self.env.sphinx_exercise_gated_registry = {}
        gated_registry = self.env.sphinx_exercise_gated_registry
        docname = self.env.docname
        if docname not in gated_registry:
            gated_registry[docname] = {
                "start": [],
                "end": [],
                "sequence": [],
                "msg": [],
                "type": "grasple-exercise",
            }
        gated_registry[self.env.docname]["start"].append(self.lineno)
        gated_registry[self.env.docname]["sequence"].append("S")
        gated_registry[self.env.docname]["msg"].append(
            f"{self.name} at line: {self.lineno}"
        )
        # Run Parent Methods
        return super().run()


class GraspleExerciseEndDirective(SphinxDirective):
    """
    A simple gated directive to mark end of an exercise

    .. exercise-end::
    """

    name = "grasple-exercise-end"

    def run(self):
        # Initialise Gated Registry
        if not hasattr(self.env, "sphinx_grasple_exercise_gated_registry"):
            self.env.sphinx_exercise_gated_registry = {}
        gated_registry = self.env.sphinx_exercise_gated_registry
        docname = self.env.docname
        if docname not in gated_registry:
            gated_registry[docname] = {
                "start": [],
                "end": [],
                "sequence": [],
                "msg": [],
                "type": "grasple-exercise",
            }
        gated_registry[self.env.docname]["end"].append(self.lineno)
        gated_registry[self.env.docname]["sequence"].append("E")
        gated_registry[self.env.docname]["msg"].append(
            f"{self.name} at line: {self.lineno}"
        )
        return [grasple_exercise_end_node()]

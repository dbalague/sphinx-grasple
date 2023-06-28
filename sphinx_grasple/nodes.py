"""
sphinx_exercise.nodes
~~~~~~~~~~~~~~~~~~~~~

Sphinx Exercise Nodes

:copyright: Copyright 2020-2021 by the Executable Books team, see AUTHORS
:licences: see LICENSE for details
"""

from sphinx.util import logging
from docutils.nodes import Node
from docutils import nodes as docutil_nodes
from sphinx import addnodes as sphinx_nodes
from sphinx.writers.latex import LaTeXTranslator
from .latex import LaTeXMarkup

logger = logging.getLogger(__name__)
LaTeX = LaTeXMarkup()


# Nodes


class grasple_exercise_node(docutil_nodes.Admonition, docutil_nodes.Element):
    gated = False


class grasple_exercise_enumerable_node(docutil_nodes.Admonition, docutil_nodes.Element):
    gated = False
    resolved_title = False


class grasple_exercise_end_node(docutil_nodes.Admonition, docutil_nodes.Element):
    pass


class grasple_exercise_title(docutil_nodes.title):
    def default_title(self):
        title_text = self.children[0].astext()
        if title_text == "Grasple Exercise" or title_text == "Grasple Exercise %s":
            return True
        else:
            return False


class grasple_exercise_subtitle(docutil_nodes.subtitle):
    pass


class exercise_latex_number_reference(sphinx_nodes.number_reference):
    pass

# Test Node Functions

def is_exercise_node(node):
    return isinstance(node, grasple_exercise_node) or isinstance(node, grasple_exercise_enumerable_node)


def is_exercise_enumerable_node(node):
    return isinstance(node, grasple_exercise_enumerable_node)


def is_extension_node(node):
    return (
        is_exercise_node(node)
        or is_exercise_enumerable_node(node)
    )

# Visit and Depart Functions

def visit_grasple_exercise_node(self, node: Node) -> None:
    if isinstance(self, LaTeXTranslator):
        label = (
            "\\phantomsection \\label{" + f"exercise:{node.attributes['label']}" + "}"
        )  # TODO: Check this resolves.
        self.body.append(label)
        self.body.append(LaTeX.visit_admonition())
    else:
        self.body.append(self.starttag(node, "div", CLASS="admonition"))
        self.body.append("\n")


def depart_grasple_exercise_node(self, node: Node) -> None:
    if isinstance(self, LaTeXTranslator):
        self.body.append(LaTeX.depart_admonition())
    else:
        self.body.append("</div>")


def visit_grasple_exercise_enumerable_node(self, node: Node) -> None:
    """
    LaTeX Reference Structure is exercise:{label} and resolved by
    exercise_latex_number_reference nodes (see below)
    """
    if isinstance(self, LaTeXTranslator):
        label = (
            "\\phantomsection \\label{" + f"exercise:{node.attributes['label']}" + "}\n"
        )
        self.body.append(label)
        self.body.append(LaTeX.visit_admonition())
    else:
        self.body.append(self.starttag(node, "div", CLASS="admonition"))
        self.body.append("\n")

def depart_grasple_exercise_enumerable_node(self, node: Node) -> None:
    if isinstance(self, LaTeXTranslator):
        self.body.append(LaTeX.depart_admonition())
    else:
        self.body.append("</div>")
        self.body.append("\n")

def visit_exercise_latex_number_reference(self, node):
    id = node.get("refid")
    text = node.astext()
    hyperref = r"\hyperref[exercise:%s]{%s}" % (id, text)
    self.body.append(hyperref)
    raise docutil_nodes.SkipNode


def depart_exercise_latex_number_reference(self, node):
    pass

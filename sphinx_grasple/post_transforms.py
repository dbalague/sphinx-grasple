import sphinx.addnodes as sphinx_nodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.builders.latex import LaTeXBuilder
from docutils import nodes as docutil_nodes

from .utils import get_node_number, find_parent
from .nodes import (
    grasple_exercise_enumerable_node,
    grasple_exercise_title,
    grasple_exercise_subtitle,
    is_exercise_node,
    exercise_latex_number_reference,
)

logger = logging.getLogger(__name__)


def build_reference_node(app, target_node):
    """
    Builds a docutil.nodes.reference object
    to a given target_node.
    """
    refuri = app.builder.get_relative_uri(
        app.env.docname, target_node.get("docname", "")
    )
    refuri += "#" + target_node.get("label")
    reference = docutil_nodes.reference(
        "",
        "",
        internal=True,
        refuri=refuri,
        anchorname="",
    )
    return reference


class UpdateReferencesToGraspleEnumerated(SphinxPostTransform):
    """
        Updates all :ref: to :numref: if used when referencing
        an enumerated exercise node.
    ]"""

    default_priority = 5

    def run(self):

        if not hasattr(self.env, "sphinx_grasple_exercise_registry"):
            return

        for node in self.document.traverse(sphinx_nodes.pending_xref):
            if node.get("reftype") != "numref":
                target_label = node.get("reftarget")
                if target_label in self.env.sphinx_grasple_exercise_registry:
                    target = self.env.sphinx_grasple_exercise_registry[target_label]
                    target_node = target.get("node")
                    if isinstance(target_node, grasple_exercise_enumerable_node):
                        # Don't Modify Custom Text
                        if node.get("refexplicit"):
                            continue
                        node["reftype"] = "numref"
                        # Get Metadata from Inline
                        inline = node.children[0]
                        classes = inline["classes"]
                        classes.remove("std-ref")
                        classes.append("std-numref")
                        # Construct a Literal Node
                        literal = docutil_nodes.literal()
                        literal["classes"] = classes
                        literal.children += inline.children
                        node.children[0] = literal


class ResolveTitlesInGraspleExercises(SphinxPostTransform):
    """
    Resolve Titles for Exercise Nodes and Enumerated Exercise Nodes
    for:
        1. Numbering
        2. Formatting Title and Subtitles into docutils.title node
    """

    default_priority = 20

    def resolve_title(self, node):
        title = node.children[0]
        if isinstance(title, grasple_exercise_title):
            updated_title = docutil_nodes.title()
            if isinstance(node, grasple_exercise_enumerable_node):
                # Numfig (HTML) will use "Exercise %s" so we just need the subtitle
                if self.app.builder.format == "latex":
                    # Resolve Title
                    node_number = get_node_number(self.app, node, "grasple-exercise")
                    title_text = self.app.config.numfig_format["grasple-exercise"] % node_number
                    updated_title += docutil_nodes.Text(title_text)
                updated_title["title"] = self.app.config.numfig_format["grasple-exercise"]
            else:
                # Use default text "Exercise"
                updated_title += title.children[0]
            # Parse Custom Titles
            if len(title.children) > 1:
                subtitle = title.children[1]
                if isinstance(subtitle, grasple_exercise_subtitle):
                    updated_title += docutil_nodes.Text(" (")
                    for child in subtitle.children:
                        updated_title += child
                    updated_title += docutil_nodes.Text(")")
            updated_title.parent = title.parent
            node.children[0] = updated_title
        node.resolved_title = True
        return node

    def run(self):

        if not hasattr(self.env, "sphinx_grasple_exercise_registry"):
            return

        for node in self.document.traverse(is_exercise_node):
            node = self.resolve_title(node)

import re
import docutils

from sphinx.transforms import SphinxTransform
from sphinx.util import logging
from sphinx.errors import ExtensionError

# from sphinx.errors import ExtensionError

from .nodes import (
    grasple_exercise_node,
    grasple_exercise_enumerable_node,
    grasple_exercise_end_node
)

logger = logging.getLogger(__name__)


class CheckGatedDirectives(SphinxTransform):
    """
    This transform checks the structure of the gated solutions
    to flag any errors in input
    """

    default_priority = 1

    def check_structure(self, registry):
        """Check Structure of the Gated Registry"""
        error = False
        docname = self.env.docname
        if docname in registry:
            start = registry[docname]["start"]
            end = registry[docname]["end"]
            sequence = "".join(registry[docname]["sequence"])
            structure = "\n  ".join(registry[docname]["msg"])
            nodetype = registry[docname]["type"]
            if len(start) > len(end):
                msg = f"The document ({docname}) is missing a {nodetype}-end directive\n  {structure}"  # noqa: E501
                logger.error(msg)
                error = True
            if len(start) < len(end):
                msg = f"The document ({docname}) is missing a {nodetype}-start directive\n  {structure}"  # noqa: E501
                logger.error(msg)
                error = True
            if len(start) == len(end):
                groups = re.findall("(SE)", sequence)
                if len(groups) != len(start):
                    msg = f"The document ({docname}) contains nested {nodetype}-start and {nodetype}-end directives\n  {structure}"  # noqa: E501
                    logger.error(msg)
                    error = True
        if error:
            msg = "[sphinx-grasple] An error has occured when parsing gated directives.\nPlease check warning messages above"  # noqa: E501
            raise ExtensionError(message=msg)

    def apply(self):
        # Check structure of all -start and -end nodes
        if hasattr(self.env, "sphinx_grasple_exercise_gated_registry"):
            self.check_structure(self.env.sphinx_grasple_exercise_gated_registry)


class MergeGatedExercises(SphinxTransform):
    """
    Transform Gated Exercise Directives into single unified
    Directives in the Sphinx Abstract Syntax Tree

    Note: The CheckGatedDirectives Transform should ensure the
    structure of the gated directives is correct before
    this transform is run.
    """

    default_priority = 10

    def find_nodes(self, label, node):
        parent_node = node.parent
        parent_start, parent_end = None, None
        for idx1, child in enumerate(parent_node.children):
            if isinstance(
                child, (grasple_exercise_node, grasple_exercise_enumerable_node)
            ) and label == child.get("label"):
                parent_start = idx1
                for idx2, child2 in enumerate(parent_node.children[parent_start:]):
                    if isinstance(child2, grasple_exercise_end_node):
                        parent_end = idx1 + idx2
                        break
                break
        return parent_start, parent_end

    def merge_nodes(self, node):
        label = node.get("label")
        parent_start, parent_end = self.find_nodes(label, node)
        if not parent_end:
            return
        parent = node.parent
        # Use Current Node and remove "-start" from class names and type
        updated_classes = [
            cls.replace("-start", "") for cls in node.attributes["classes"]
        ]
        node.attributes["classes"] = updated_classes
        node.attributes["type"] = node.attributes["type"].replace("-start", "")
        # Attach content to section
        content = node.children[-1]
        for child in parent.children[parent_start + 1 : parent_end]:
            content += child
        # Clean up Parent Node including :exercise-end:
        for child in parent.children[parent_start + 1 : parent_end + 1]:
            parent.remove(child)

    def apply(self):
        # Process all matching exercise and exercise-enumerable (gated=True)
        # and exercise-end nodes
        for node in self.document.traverse(grasple_exercise_node):
            if node.gated:
                self.merge_nodes(node)
            node.gated = False
        for node in self.document.traverse(grasple_exercise_enumerable_node):
            if node.gated:
                self.merge_nodes(node)
            node.gated = False

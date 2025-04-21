from dataclasses import dataclass, field
from typing import Dict, Set, Tuple
from collections import defaultdict

from core.models.graph import Graph


@dataclass
class GraphDifference:
    added_nodes: Set[str] = field(default_factory=set)
    removed_nodes: Set[str] = field(default_factory=set)
    changed_nodes: Dict[str, Dict[str, Tuple[str, str]]] = field(default_factory=dict)
    added_edges: Dict[str, Set[Tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    removed_edges: Dict[str, Set[Tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))


class GraphComparator:

    @staticmethod
    def get_difference(old_graph: Graph, new_graph: Graph) -> GraphDifference:
        diff = GraphDifference()

        old_nodes = set(old_graph.nodes.keys())
        new_nodes = set(new_graph.nodes.keys())

        diff.added_nodes = new_nodes - old_nodes
        diff.removed_nodes = old_nodes - new_nodes

        common_nodes = old_nodes & new_nodes
        for node_id in common_nodes:
            old_node = old_graph.nodes[node_id]
            new_node = new_graph.nodes[node_id]

            changes = {}

            if old_node.type != new_node.type:
                changes["type"] = (old_node.type, new_node.type)

            old_labels = set(old_node.meta.labels)
            new_labels = set(new_node.meta.labels)

            if old_labels != new_labels:
                changes["labels"] = (list(old_labels - new_labels), list(new_labels - old_labels))

            if changes:
                diff.changed_nodes[node_id] = changes

        for node_id in common_nodes:
            old_edges = {(e.id, e.type) for e in old_graph.nodes[node_id].edges}
            new_edges = {(e.id, e.type) for e in new_graph.nodes[node_id].edges}

            added = new_edges - old_edges
            removed = old_edges - new_edges

            if added:
                diff.added_edges[node_id].update(added)
            if removed:
                diff.removed_edges[node_id].update(removed)

        for node_id in diff.added_nodes:
            for edge in new_graph.nodes[node_id].edges:
                diff.added_edges[node_id].add((edge.id, edge.type))

        for node_id in diff.removed_nodes:
            for edge in old_graph.nodes[node_id].edges:
                diff.removed_edges[node_id].add((edge.id, edge.type))

        return diff

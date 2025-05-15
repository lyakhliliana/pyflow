from collections import defaultdict
from copy import deepcopy
import logging
from typing import List, Set, Dict

from core.models.graph import Graph
from core.models.edge import Edge, TypeEdge
from core.models.node import Node, TypeNode
from core.models.common import TypeSource

logger = logging.getLogger(__name__)

OTHER_NODE_NAME = "other_unknown"


class GraphContractor:

    def __init__(self, graph: Graph):
        self.contracted_nodes: Dict[str, Set[str]] = defaultdict(set)
        self.node_contracted_in: Dict[str, Set[str]] = defaultdict(set)
        self.combine_other = False
        self.graph: Graph = graph
        self.con_graph: Graph = deepcopy(graph)

    def contract_graph(self, node_ids: List[str], combine_other: bool = False) -> Graph:
        """
        Creates a new graph with contracted nodes based on contain edges.
        
        Args:
            graph: Original graph to contract
            node_ids: List of node IDs to consider for contract
            
        Returns:
            New graph with contracted nodes
        """
        self.combine_other = combine_other
        for node_id in node_ids:
            self._contract_by_node(node_id, node_ids)

        if self.combine_other:
            self._process_other()

        return self.con_graph

    def _contract_by_node(self, node_id: str, node_ids: List[str]):
        if node_id in self.contracted_nodes:
            logger.warning(f"Node {node_id} was processed earlier.")
            return

        current_node = self.graph.get_node(node_id)
        if not current_node or current_node.type != TypeNode.ARC_ELEMENT:
            logger.warning(f"Node {node_id} not found or type not equal {TypeNode.ARC_ELEMENT}")
            return

        contracted_node_ids = []
        for edge in self.graph.get_edges_out(node_id):
            if edge.type == TypeEdge.CONTAIN:
                contracted_node_ids.append(edge.dest)

        for contracted_node_id in contracted_node_ids:
            self._process_contracted_node(node_id, contracted_node_id)

        for contracted_node_id in contracted_node_ids:
            self.contracted_nodes[node_id].add(contracted_node_id)
            self.node_contracted_in[contracted_node_id].add(node_id)

        for contracted_node_id in contracted_node_ids:
            edges_in = self.graph.get_edges_in(contracted_node_id)
            arc_elems = set([
                edge.src for edge in edges_in
                if edge.type == TypeEdge.CONTAIN and self.graph.get_node(edge.src) == TypeNode.ARC_ELEMENT
            ])
            node_ids = set(node_ids)

            if len(arc_elems - node_ids) > 0:
                continue
            else:
                self.con_graph.remove_node(contracted_node_id)

    def _process_contracted_node(self, node_id: str, contracted_node_id: str):

        if contracted_node_id in self.node_contracted_in:
            coupling_elements = self.node_contracted_in[contracted_node_id]
            for coupling_element in coupling_elements:
                con_edge = Edge(src=node_id, dest=coupling_element, type=TypeEdge.COUPLING, source=TypeSource.HAND)
                self.con_graph.add_edge(con_edge)
                con_edge = Edge(src=coupling_element, dest=node_id, type=TypeEdge.COUPLING, source=TypeSource.HAND)
                self.con_graph.add_edge(con_edge)

        edges_out = self.graph.get_edges_out(contracted_node_id)
        edges_in = self.graph.get_edges_in(contracted_node_id)

        for edge_out in edges_out:
            if edge_out.dest not in self.node_contracted_in:
                con_edge = Edge(src=node_id, dest=edge_out.dest, type=edge_out.type, source=TypeSource.HAND)
                self.con_graph.add_edge(con_edge)

            else:
                for dest in self.node_contracted_in[edge_out.dest]:
                    con_edge = Edge(src=node_id, dest=dest, type=edge_out.type, source=TypeSource.HAND)
                    self.con_graph.add_edge(con_edge)

        for edge_in in edges_in:
            if self.graph.nodes[edge_in.src].type == TypeNode.ARC_ELEMENT:
                continue

            if edge_in.src not in self.node_contracted_in:
                con_edge = Edge(src=edge_in.src, dest=node_id, type=edge_in.type, source=TypeSource.HAND)
                self.con_graph.add_edge(con_edge)

            else:
                for src in self.node_contracted_in[edge_in.src]:
                    con_edge = Edge(src=src, dest=node_id, type=edge_in.type, source=TypeSource.HAND)
                    self.con_graph.add_edge(con_edge)

    def _process_other(self):
        other_nodes = [node.id for node in self.graph.get_all_nodes() if node.id not in self.node_contracted_in]

        if len(other_nodes) == 0:
            return

        self.con_graph.add_node(
            Node(
                id=OTHER_NODE_NAME,
                name=OTHER_NODE_NAME,
                type=TypeNode.ARC_ELEMENT,
                source=TypeSource.HAND,
            ))

        for other in other_nodes:
            self._process_contracted_node(OTHER_NODE_NAME, other)

        for other in other_nodes:
            self.contracted_nodes[OTHER_NODE_NAME].add(other)
            self.node_contracted_in[other].add(OTHER_NODE_NAME)
            self.con_graph.remove_node(other)

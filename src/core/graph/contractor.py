from collections import defaultdict
from copy import deepcopy
import logging
from typing import List, Set, Dict
from core.models.graph import Graph
from core.models.edge import Edge, TypeEdge, TypeSourceEdge
from core.models.node import TypeNode

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
            self._contract_by_node(node_id)
        return self.con_graph

    def _contract_by_node(self, node_id: str):
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
            self.con_graph.remove_node(contracted_node_id)

    def _process_contracted_node(self, node_id: str, contracted_node_id: str):

        if contracted_node_id in self.node_contracted_in:
            coupling_elements = self.node_contracted_in[contracted_node_id]
            for coupling_element in coupling_elements:
                con_edge = Edge(src=node_id, dest=coupling_element, type=TypeEdge.COUPLING, source=TypeSourceEdge.HAND)
                self.con_graph.add_edge(con_edge)
                con_edge = Edge(src=coupling_element, dest=node_id, type=TypeEdge.COUPLING, source=TypeSourceEdge.HAND)
                self.con_graph.add_edge(con_edge)

        edges_out = self.graph.get_edges_out(contracted_node_id)
        edges_in = self.graph.get_edges_in(contracted_node_id)

        for edge_out in edges_out:
            if edge_out.dest not in self.node_contracted_in:
                con_edge = Edge(src=node_id, dest=edge_out.dest, type=edge_out.type, source=TypeSourceEdge.HAND)
                self.con_graph.add_edge(con_edge)

            else:
                for dest in self.node_contracted_in[edge_out.dest]:
                    con_edge = Edge(src=node_id, dest=dest, type=edge_out.type, source=TypeSourceEdge.HAND)
                    self.con_graph.add_edge(con_edge)

        for edge_in in edges_in:
            if self.graph.nodes[edge_in.src].type == TypeNode.ARC_ELEMENT:
                continue

            if edge_in.src not in self.node_contracted_in:
                con_edge = Edge(src=edge_in.src, dest=node_id, type=edge_in.type, source=TypeSourceEdge.HAND)
                self.con_graph.add_edge(con_edge)

            else:
                for src in self.node_contracted_in[edge_in.src]:
                    con_edge = Edge(src=src, dest=node_id, type=edge_in.type, source=TypeSourceEdge.HAND)
                    self.con_graph.add_edge(con_edge)

from copy import deepcopy

from core.models.graph import Graph

DIFFERENCE_STATUS_FIELD = 'difference_status'


class TypeDiff(str):
    NEW = 'new'
    DELETED = 'deleted'

    CHANGED = 'changed'
    UNCHACHGED = 'unchanged'


class GraphComparator:

    @staticmethod
    def get_difference(old_graph: Graph, new_graph: Graph) -> Graph:
        """
        Compute a diff-annotated graph showing changes from old_graph to new_graph.

        Args:
            old_graph (Graph): The original graph.
            new_graph (Graph): The updated graph.

        Returns:
            Graph: A graph whose nodes and edges carry a meta flag of type TypeDiff.
        """

        result_graph = Graph()

        old_nodes = set(old_graph.nodes.keys())
        new_nodes = set(new_graph.nodes.keys())
        added_nodes = new_nodes - old_nodes
        deleted_nodes = old_nodes - new_nodes
        common_nodes = old_nodes & new_nodes

        # Add new nodes
        for node_id in added_nodes:
            node = deepcopy(new_graph.get_node(node_id))
            node.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.NEW
            result_graph.add_node(node)

        # Add deleted nodes
        for node_id in deleted_nodes:
            node = deepcopy(old_graph.get_node(node_id))
            node.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.DELETED
            result_graph.add_node(node)

        # Add common nodes, marking changed or unchanged
        for node_id in common_nodes:
            old_node = old_graph.get_node(node_id)
            new_node = deepcopy(new_graph.get_node(node_id))
            status = TypeDiff.CHANGED if old_node.hash != new_node.hash else TypeDiff.UNCHACHGED
            new_node.meta[DIFFERENCE_STATUS_FIELD] = status
            result_graph.add_node(new_node)

        # Determine edge differences for new nodes
        for node_id in added_nodes:
            for edge in new_graph.get_edges_out(node_id):
                result_edge = deepcopy(edge)
                result_edge.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.NEW
                result_graph.add_edge(result_edge)

        # Determine edge differences for deleted nodes
        for node_id in deleted_nodes:
            for edge in old_graph.get_edges_out(node_id):
                result_edge = deepcopy(edge)
                result_edge.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.DELETED
                result_graph.add_edge(result_edge)

        # Determine edge differences for nodes present in both graphs
        for node_id in common_nodes:
            old_edges = set(old_graph.get_edges_out(node_id))
            new_edges = set(new_graph.get_edges_out(node_id))

            added_edges = new_edges - old_edges
            deleted_edges = old_edges - new_edges
            common_edges = old_edges & new_edges

            for edge in added_edges:
                result_edge = deepcopy(edge)
                result_edge.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.NEW
                result_graph.add_edge(result_edge)

            for edge in deleted_edges:
                result_edge = deepcopy(edge)
                result_edge.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.DELETED
                result_graph.add_edge(result_edge)

            for edge in common_edges:
                result_edge = deepcopy(edge)
                result_edge.meta[DIFFERENCE_STATUS_FIELD] = TypeDiff.UNCHACHGED
                result_graph.add_edge(result_edge)

        return result_graph

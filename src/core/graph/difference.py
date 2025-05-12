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
        The method analyzes differences between two graphs and marks each node and edge
        with a status in the meta field 'difference_status'. The status can be one of:
        
        Status values in meta['difference_status']:
        - 'new': Element exists only in new_graph
        - 'deleted': Element exists only in old_graph
        - 'changed': Element exists in both graphs but has different content (determined by hash comparison)
        - 'unchanged': Element exists in both graphs with identical content

        The method processes both nodes and edges:
        - For nodes: compares their presence and content between graphs
        - For edges: compares their presence and relationships between graphs
        
        All statuses are stored in the meta field of each node and edge, allowing
        for easy identification of what changed between the two graphs.

        Args:
            old_graph (Graph): The original graph to compare from
            new_graph (Graph): The updated graph to compare to

        Returns:
            Graph: Each element's meta['difference_status'] field indicates its status
                   in the comparison between old_graph and new_graph.
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

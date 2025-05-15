from core.models.edge import TypeEdge
from core.models.graph import Graph
from core.models.node import ADDITIONAL_NODE_TYPES, CODE_NODE_TYPES, ROOT_NODE_NAME
from utils.hash import stable_hash_from_hashes


class Hasher:

    @staticmethod
    def recalculate(graph: Graph) -> Graph:
        """
        Recalculates hashes for all nodes in the graph.
        
        This function performs a two-phase hash recalculation:
        1. First phase: Calculates structure hashes for non-code nodes
        2. Second phase: Calculates additional hashes for nodes with additional types
        
        The function uses recursive traversal to compute hashes based on the graph structure
        and node relationships.
        
        Args:
            graph (Graph): The graph object containing nodes and edges to recalculate hashes for
            
        Returns:
            Graph: The same graph object with updated hashes for all nodes
        """

        def recursive_structure_hash(cur_id: str = ROOT_NODE_NAME) -> str:
            cur_node = graph.get_node(cur_id)

            if cur_node.type in CODE_NODE_TYPES:
                return cur_node.hash

            hashes = []
            contain_edges = graph.get_edges_out(cur_id)
            for edge in contain_edges:
                if edge.type != TypeEdge.CONTAIN:
                    continue
                hash_node_id = recursive_structure_hash(edge.dest)
                hashes.append(hash_node_id)

            cur_node.hash = stable_hash_from_hashes(hashes)
            return cur_node.hash

        def recursive_additional_hash(cur_id: str = ROOT_NODE_NAME) -> str:
            cur_node = graph.get_node(cur_id)

            if cur_node.type not in ADDITIONAL_NODE_TYPES or cur_node.hash != "":
                return cur_node.hash

            hashes = []
            contain_edges = graph.get_edges_out(cur_id)
            for edge in contain_edges:
                if edge.type != TypeEdge.CONTAIN:
                    continue
                hash_node_id = recursive_additional_hash(edge.dest)
                hashes.append(hash_node_id)

            cur_node.hash = stable_hash_from_hashes(hashes)
            return cur_node.hash

        for node in graph.get_all_nodes():
            if node.type not in CODE_NODE_TYPES:
                node.hash = ""

        recursive_structure_hash()

        for node in graph.get_all_nodes():
            if node.type in ADDITIONAL_NODE_TYPES:
                recursive_additional_hash(node.id)

        return graph

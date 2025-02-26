from src.entities.common.graph import Graph
from src.entities.common.edge import Edge, TypeEdge
from src.entities.common.node import TypeNode


class FilterMode:
    FULL = 'full'
    STRUCT = 'struct'
    OBJECT_LINKS = 'object_links'
    FILE_LINKS = 'file_links'


class Filter:

    @staticmethod
    def get_object_links(graph: Graph) -> Graph:
        filtered_graph = Graph()
        for _, node in graph.nodes.items():
            if node.type not in [TypeNode.BODY, TypeNode.CLASS, TypeNode.FUNC]:
                continue
            filtered_graph.add_node(node)

        for _, node in filtered_graph.nodes.items():
            filtered_links = [
                link for link in node.links if link.type in [
                    TypeEdge.USE] and link.id in filtered_graph.nodes]
            node.links = filtered_links

        return filtered_graph

    @staticmethod
    def get_struct(graph: Graph) -> Graph:
        filtered_graph = Graph()

        for _, node in graph.nodes.items():
            filtered_links = [link for link in node.links if link.type in [
                TypeEdge.CONTAIN] and link.id in graph.nodes]
            node.links = filtered_links
            filtered_graph.add_node(node)

        return filtered_graph

    @staticmethod
    def full(graph: Graph) -> Graph:
        filtered_graph = Graph()

        for _, node in graph.nodes.items():
            filtered_links = [link for link in node.links if link.id in graph.nodes]
            node.links = filtered_links
            filtered_graph.add_node(node)

        return filtered_graph
    
    @staticmethod
    def get_files_links(graph: Graph) -> Graph:
        filtered_graph = Graph()
        for _, node in graph.nodes.items():
            if node.type != TypeNode.FILE:
                continue
            filtered_graph.add_node(node)

        for _, node in filtered_graph.nodes.items():
            new_links = set()
            for link in node.links:
                cur_object = graph.nodes[link.id]
                for object_link in cur_object.links:
                    file_where_object_exist = object_link.id.split('#')[0]
                    if object_link.type == TypeEdge.USE and node.name != file_where_object_exist:
                        new_links.add(file_where_object_exist)
                    
            node.links = [Edge(link, TypeEdge.USE) for link in new_links]

        return filtered_graph


FILTER_BY_MODE = {
    FilterMode.FULL: Filter.full,
    FilterMode.STRUCT: Filter.get_struct,
    FilterMode.OBJECT_LINKS: Filter.get_object_links,
    FilterMode.FILE_LINKS: Filter.get_files_links
}

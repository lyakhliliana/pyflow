import json
import networkx as nx
from pyvis.network import Network

# Загрузка данных из JSON
file_path = "tmp/results/output.json"
with open(file_path, "r", encoding="utf-8") as f:
    graph_data = json.load(f)

# Создание графа
G = nx.DiGraph()

for node, data in graph_data.items():
    # if data['type'] == 'file':
        G.add_node(node, **data)
        for link in data["links"]:
            G.add_edge(node, link['id'], label=link['type'])

# Визуализация с pyvis
net = Network(notebook=True, cdn_resources="remote", directed=True)
net.from_nx(G)

# Настройка визуализации
net.show_buttons(filter_=['physics'])  # Добавляем кнопки для настройки
net.show("view/pyvis/graph.html")  # Сохраняем граф в HTML-файл
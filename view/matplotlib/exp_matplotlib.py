import json
import networkx as nx
import matplotlib.pyplot as plt

# Загрузка данных из JSON
file_path = "tmp/results/output.json"
with open(file_path, "r", encoding="utf-8") as f:
    graph_data = json.load(f)

# Создание графа
G = nx.DiGraph()

for node, data in graph_data.items():
    if data['type'] == 'file':
        G.add_node(node, **data)
        for link in data["links"]:
            G.add_edge(node, link['id'], label=link['type'])

# Рисуем граф
pos = nx.spring_layout(G)  # Расположение узлов
nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1500, font_size=10, arrows=True)

# Подписываем ребра
edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")

# Показываем граф
plt.show()
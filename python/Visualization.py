import networkx as nx
import matplotlib.pyplot as pyplot
from operator import itemgetter

def EventGraph (protagonist, matrix, cutoff=0, directed=False):
	# Determine if directed graph
	if (directed):
		G = nx.DiGraph()
	else:
		G = nx.Graph()

	# Extract list of narrative events (verbs)
	events = protagonist.events

	# Add nodes (verbs) to graph
	for verb in events.keys():
		G.add_node(verb)

	# Add edges (pmi scores) to graph
	for i in range(0, len(events)):
		for j in range(0, len(events)):
			w = matrix[i][j]
			if w > 0:
				G.add_edge(events[i][0], events[j][0], weight=w)

	# Compute degree centrality for each node
	if (len(G) > 1):
		dc = nx.degree_centrality(G)
		nx.set_node_attributes(G, 'degree_centrality', dc)
		G.graph['degree_centrality'] = dc

	# Format edge labels
	edge_labels = dict([((u,v,), '%.3g' % d['weight']) for u,v,d in G.edges(data=True)]);
	G.graph['edge_labels'] = edge_labels

	return G

def highest_degree_centrality (graph, top=10):
	sdc = sorted(graph.graph['degree_centrality'].items(), key=itemgetter(1), reverse=True)
	return sdc
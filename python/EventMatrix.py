import numpy as np
from Protagonist import *

class EventMatrix:

	def __init__(self, narrative):
		self.adjMatrix = self.buildAdjMatrix(narrative)
		self.pmiMatrix = self.buildPmiMatrix(narrative)

	def buildAdjMatrix (self, narrative):
		n = len(narrative.events)
		adjMatrix = np.zeros((n, n), dtype=np.int)
		for p in narrative.pairs.keys():
			x = narrative.events[p[0]][0]
			y = narrative.events[p[1]][0]
			adjMatrix[x][y] += narrative.pairs[p[0], p[1]]
		return adjMatrix

	def buildPmiMatrix (self, narrative):
		n = self.adjMatrix.shape[0]
		pmiMatrix = np.zeros((n, n), dtype=np.dtype('f8'))
		for i in range(0, n):
			for j in range(0, n):
				count = self.adjMatrix[i][j]
				if (count > 0):
					v1 = narrative.events[i][1]
					v2 = narrative.events[j][1]
					M = narrative.numPairs()
					N = narrative.numEvents()
					pmiMatrix[i][j] = self.pmi(count, v1, v2, M, N)
		return pmiMatrix

	def pmi (self, c, v1, v2, M, N):
		score = np.log (((c * N * N) + 0.0) /
						(v1 * v2 * M))
		return score * self.discount(c, v1, v2)

	def discount (self, c, v1, v2):
		v = min(v1, v2)
		return ((c * v + 0.0) / 
				((c + 1) * (v + 1)))


from Protagonist import *
from EventMatrix import *
from Visualization import *
import pickle

def induct (entityVerbMap):
	"""
	Narrative Event Induction: turns each entity in a entity-verb(s) mapping 
	into a narrative event representation.
	"""
	protags = {}
	for ent, vlist in entityVerbMap.iteritems():
		events = Events()
		pairs = EventPairs()
		for verbs in vlist:
			for i in range(0, len(verbs)):
				events.append(verbs[i])
				for j in range(i+1, len(verbs)):
					if (verbs[i] != verbs[j]):
						pairs.append((verbs[i], verbs[j]))
		protags[ent] = NarrativeEvent(ent, events, pairs)
	return protags

def serialize (obj, path):
	pickle.dump(obj, open(path, 'w'))

class NarrativeEvent:

	def __init__(self, name, events, pairs):
		self.name = name
		self.protagonist = Protagonist(name, events, pairs)
		self.eventMatrix = EventMatrix(self.protagonist)
		self.adjGraph = EventGraph(self.protagonist, self.eventMatrix.adjMatrix)
		self.pmiGraph = EventGraph(self.protagonist, self.eventMatrix.pmiMatrix)

	def eventChain (self, head, size=6):
		n = self.eventMatrix.pmiMatrix.shape[0]
		events = [head]
		while len(events) < size:
			score = [0]*n
			for verbId in events:
				for i in range(0,n):
					if i not in events:
						score[i] += self.eventMatrix.pmiMatrix[verbId][i] + \
									self.eventMatrix.pmiMatrix[i][verbId]
			best = max(score)
			if best > 0:
				best = score.index(best)
				events.append(best)
			else:
				break
		return events

	def eventTypes (self):
		return self.protagonist.events

	def eventPairs (self):
		return self.protagonist.pairs

	def adjMatrix (self):
		return self.eventMatrix.adjMatrix

	def pmiMatrix (self):
		return self.eventMatrix.pmiMatrix
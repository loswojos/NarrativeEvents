import sys
from os import listdir
from os.path import isfile, join
from collections import defaultdict, namedtuple
from math import log
import corenlp as clnp

class NarrativeBank:

	def __init__(self, dep_dir):
		self.Event = namedtuple("Event", ["verb", "entity"])
		self.events = defaultdict(int)
		self.eventPairs = defaultdict(lambda: defaultdict(int))
		self.build(dep_dir)

	def pmi (self, entity, verb1, verb2):
		c = self.eventPairs[entity][(verb1, verb2)]
		N = self.num_events(entity)
		M = self.num_pairs(entity)
		v1 = self.events[self.Event(verb=verb1, entity=entity)]
		v2 = self.events[self.Event(verb=verb2, entity=entity)]

		score = log (((c * N * N) + 0.0) /
						(v1 * v2 * M))
		return score * self.discount(c, v1, v2)

	def discount (self, c, v1, v2):
		v = min(v1, v2)
		return ((c * v + 0.0) / 
				((c + 1) * (v + 1)))

	def num_events (self, entity):
		return sum([self.events[x] for x in self.events_for(entity)])

	def unique_events (self, entity):
		return len([self.events[x] for x in self.events_for(entity)])

	def events_for (self, entity):
		return [x for x in self.events.keys() if x.entity==entity]

	def num_protags (self, verb):
		return sum([self.events[x] for x in self.entities_in(verb)])

	def entities_in (self, verb):
		return [x for x in self.events.keys() if x.verb==verb]

	def num_pairs (self, entity):
		return sum(self.eventPairs[entity].values())

	def unique_pairs (self, entity):
		return len(self.eventPairs[entity].values())

	def build (self, dep_dir):
		"""
		Extracts a set of valid narrative events from a corpus, groups by entity name,
		and returns an entity-verb(s) mapping.
		"""

		Event = namedtuple("Event", ["verb", "entity"])

		for i, path in enumerate(listdir(dep_dir)):
			f = join(dep_dir, path)
			if isfile(f) and ('xml' in path):
				# try:
				doc = clnp.Document(f)
				for ent, verbs in self.aggregate(doc).iteritems():
					if len(verbs) > 1:
						for i in range(0, len(verbs)):
							self.events[Event(verb=verbs[i], entity=ent)] += 1
							for j in range(i+1, len(verbs)):
								if (verbs[i] != verbs[j]):
									self.eventPairs[ent][(verbs[i], verbs[j])] += 1
							
				# except Exception, err:
					# sys.stderr.write('FILE: %s\n' % f)
					# sys.stderr.write('ERROR: %s\n' % str(err))

	def aggregate (self, doc, word=False):
		"""
		Extracts a set of valid narrative events from a document, groups by entity name,
		and returns an entity-verb(s) mapping.
		"""
		entityVerbMap = defaultdict(list)
		for sent in doc:
			for dep in self.constrain(sent.deps):
				if (word):
					entityVerbMap[dep.dep.word.lower()].append(dep.gov.word.lower())
				else:
					entityVerbMap[dep.dep.lem.lower()].append(dep.gov.lem.lower())
		return entityVerbMap

	def constrain (self, dgraph):
		"""
		Searches through Dependency Graph list of dependency relations and returns a list
		of valid narrative events, i.e. relations that meet the following constraints:
		 (a) Relation Type: Narrative
		 (b) Governor POS: Verb
		 (c) Dependent POS: Noun
		"""
		events = []
		for dep in dgraph:
			if dep.type in self.narrativeRelations():
				if dep.gov.pos in self.verbTags():
					if dep.dep.pos in self.nounTags():
						events.append(dep)
		return events

	def narrativeRelations (self):
		"""
		Returns list of narrative dependency relations in Stanford typed dependencies manual.
		"""
		return ['nsubj', 'xsubj', 'dobj', 'iobj', 'agent', 'nsubjpass']

	def verbTags (self):
		"""
		Returns list of verb POS tags in Penn Treebank.
		"""
		return ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

	def nounTags (self):
		"""
		Returns list of noun POS tags in Penn Treebank.
		"""
		return ['NN', 'NNS', 'NNP', 'NNPS']
import sys
from os import listdir
from os.path import isfile, join
from collections import defaultdict, namedtuple
from math import log
import corenlp as clnp

class NarrativeBank:

	def __init__(self, dep_dir):
		self.events = defaultdict(int)
		self.pairs = defaultdict(int)
		self.build(dep_dir)

	# PMI -------------------------------------------------------------------------------

	def pmi (self, entity, verb1, verb2):		
		cooccur = self.cooccur(entity, verb1, verb2)
		num_events = self.num_events(entity)
		num_pairs = self.num_pairs(entity)
		count1 = self.count(verb1, entity)
		count2 = self.count(verb2, entity)

		score = log (((cooccur * num_events * num_events) + 0.0) / 
						(count1 * count2 * num_pairs))

		return score * self.discount(cooccur, count1, count2)

	def discount (self, c, v1, v2):
		v = min(v1, v2)
		return ((c * v + 0.0) / ((c + 1) * (v + 1)))

	# Counts ----------------------------------------------------------------------------

	def count (self, verb, entity):
		Event = namedtuple("Event", ["verb", "entity"])
		return self.events[Event(verb=verb, entity=entity)]

	def cooccur (self, entity, verb1, verb2):
		Pair = namedtuple("Pair", ["entity", "verb1", "verb2"])
		return self.pairs[Pair(entity=entity, verb1=verb1, verb2=verb2)]

	# Events methods -------------------------------------------------------------------

	def num_events (self, entity):
		return sum([self.events[x] for x in self.events_for(entity)])

	def events_for (self, entity):
		return [x for x in self.events.keys() if x.entity==entity]

	def num_protags (self, verb):
		return sum([self.events[x] for x in self.entities_in(verb)])

	def entities_in (self, verb):
		return [x for x in self.events.keys() if x.verb==verb]

	# Pairs methods --------------------------------------------------------------------

	def num_pairs (self, entity):
		return sum([self.pairs[x] for x in self.pairs_for(entity)])

	def pairs_for (self, entity):
		return [x for x in self.pairs.keys() if x.entity==entity]

	def num_event_pairs (self, verb1, verb2):
		return sum([self.pairs[x] for x in self.pairs_involving(verb1, verb2)])

	def pairs_involving (self, verb1, verb2):
		return [x for x in self.pairs.keys() if x.verb1==verb1 and x.verb2==verb2]

	#-----------------------------------------------------------------------------------

	def build (self, dep_dir):
		"""
		Extracts a set of valid narrative events from a corpus, groups by entity name,
		and returns an entity-verb(s) mapping.
		"""

		Event = namedtuple("Event", ["verb", "entity"])
		Pair = namedtuple("Pair", ["entity", "verb1", "verb2"])

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
									self.pairs[Pair(entity=ent, verb1=verbs[i], verb2=verbs[j])] += 1
							
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
					entityVerbMap[dep.dep.word].append(dep.gov.word)
				else:
					entityVerbMap[dep.dep.lem].append(dep.gov.lem)
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
import sys
from os import listdir
from os.path import isfile, join
from collections import defaultdict
import corenlp_xml

# dep_dir: Directory containing xml files annotated by Stanford Dependency Parser

def build (dep_dir):
	"""
	Extracts a set of valid narrative events from a corpus, groups by entity name,
	and returns an entity-verb(s) mapping.
	"""

	entityVerbMap = defaultdict(list)

	for i, path in enumerate(listdir(dep_dir)):
		f = join(dep_dir, path)
		if isfile(f) and ('xml' in path):
			try:
				doc = corenlp_xml.Document(f)
				for ent, vlist in aggregate(doc).iteritems():
					if len(vlist) > 1:
						entityVerbMap[ent].append(vlist)
			except Exception, err:
				sys.stderr.write('FILE: %s\n' % f)
				sys.stderr.write('ERROR: %s\n' % str(err))

	return entityVerbMap

def aggregate (doc, word=False):
	"""
	Extracts a set of valid narrative events from a document, groups by entity name,
	and returns an entity-verb(s) mapping.
	"""
	entityVerbMap = defaultdict(list)
	for sent in doc.sentences:
		dgraph = sent.get_dependency_graph()
		for dep in constrain(dgraph):
			if (word):
				entityVerbMap[dep.dep.word].append(dep.gov.word)
			else:
				entityVerbMap[dep.dep.lem].append(dep.gov.lem)
	return entityVerbMap

def constrain (dgraph):
	"""
	Searches through Dependency Graph list of dependency relations and returns a list
	of valid narrative events, i.e. relations that meet the following constraints:
	 (a) Relation Type: Narrative
	 (b) Governor POS: Verb
	 (c) Dependent POS: Noun
	"""
	events = []
	for dep in dgraph:
		if dep.type in narrativeRelations():
			if dep.gov.pos in verbTags():
				if dep.dep.pos in nounTags():
					events.append(dep)
	return events

def narrativeRelations ():
	"""
	Returns list of narrative dependency relations in Stanford typed dependencies manual.
	"""
	return ['nsubj', 'xsubj', 'dobj', 'iobj', 'agent', 'nsubjpass']

def verbTags ():
	"""
	Returns list of verb POS tags in Penn Treebank.
	"""
	return ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

def nounTags ():
	"""
	Returns list of noun POS tags in Penn Treebank.
	"""
	return ['NN', 'NNS', 'NNP', 'NNPS']
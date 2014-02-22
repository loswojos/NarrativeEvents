from collections import defaultdict

class Protagonist:

	def __init__(self, name, events, pairs):
		self.name = name
		self.events = events
		self.pairs = pairs

	def numPairs (self):
		return self.pairs.numPairs()

	def numEvents (self):
		return self.events.numEvents()

	def uniquePairs (self):
		return self.pairs.uniquePairs()

	def uniqueEvents (self):
		return self.events.uniqueEvents()

class Events:

	def __init__(self):
		self.verbs = {}
		self.vid = {}

	def __len__(self):
		return len(self.verbs)

	def __contains__(self, key):
		return key in self.verbs

	def __setitem__(self, key, value):
		self.verbs[key] = value
		self.vid[value[0]] = (key, value[1])

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.verbs[key]
		elif isinstance(key, int):
			return self.vid[key]

	def __str__(self):
		return str(self.verbs)

	def append (self, item):
		if item not in self:
			self[item] = (len(self), 1)
		else:
			x, y = self[item]
			self[item] = (x, (y+1))

	def numEvents (self):
		return sum([x[1] for x in self.verbs.values()])

	def uniqueEvents (self):
		return len(self.verbs.keys())

	def keys (self):
		return self.verbs.keys()

	def items (self):
		return self.verbs.items()

class EventPairs:

	def __init__(self):
		self.pairs = defaultdict(dict)

	def __len__(self):
		return len(self.pairs)

	def __contains__(self, key):
		return key in self.pairs

	def __setitem__(self, key, value):
		self.pairs[key] = value

	def __getitem__(self, key):
		if isinstance(key, str):
			return [x for x in self.keys() if key in x]
		return self.pairs[key]

	def __str__(self):
		return str(self.pairs)

	def append (self, item):
		if item in self:
			self[item] += 1
		else:
			self[item] = 1

	def numPairs (self):
		return sum(self.pairs.values())

	def uniquePairs (self):
		return len(self.pairs.keys())

	def keys (self):
		return self.pairs.keys()

	def items (self):
		return self.pairs.items()
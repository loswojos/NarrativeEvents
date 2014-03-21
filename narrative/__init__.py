import sys
from os import listdir
from os.path import isfile, join
from collections import defaultdict, namedtuple
from math import log
import corenlp as clnp
import time
from itertools import izip
import corenlp

Event = namedtuple("Event", ["verb", "entity"])
Pair = namedtuple("Pair", ["entity", "verb1", "verb2"])


class NarrativeBank:

    def __init__(self, filelist=None, mode='dep'):

        self.noun_tags = [u'NN', u'NNS', u'NNP', u'NNPS']
        self.verb_tags = [u'VB', u'VBD', u'VBG', u'VBN', u'VBP', u'VBZ']
        self.relations = [u'nsubj', u'xsubj', u'dobj',
                          u'iobj', u'agent', u'nsubjpass']

        self._mode = mode
        self.events = defaultdict(int)
        self.pairs = defaultdict(int)
        if filelist is not None:
            self.add_filelist(filelist)

    # PMI --------------------------------------------------------------------

    def pmi(self, verb1, verb2, entity=None):

        if entity:
            # Protag-wise
            cooccur = self.cooccur(verb1, verb2, entity)
            num_events = self.num_events(entity)
            num_pairs = self.num_pairs(entity)
            count1 = self.count(verb1, entity)
            count2 = self.count(verb2, entity)
        else:
            # Corpus-wide
            cooccur = self.num_event_pairs(verb1, verb2)
            num_events = sum(self.events.values())
            num_pairs = sum(self.pairs.values())
            count1 = self.num_protags(verb1)
            count2 = self.num_protags(verb2)

        if cooccur > 0:
            score = log(cooccur * num_events * float(num_events) /
                        (count1 * count2 * num_pairs))
            return score * self.discount(cooccur, count1, count2)
        else:
            return None

    def discount(self, c, v1, v2):
        v = min(v1, v2)
        return ((c * v + 0.0) / ((c + 1) * (v + 1)))

    # Chain ------------------------------------------------------------------

    def chain(self, head, entity, size=6, reverse=False):
        events = [head]
        while len(events) < size:
            score = defaultdict(float)

            for verb1 in events:
                for pair, count in self.pairs.items():
                    if count > 0 and pair.entity == entity:
                        if pair.verb1 == verb1 and pair.verb2 not in events:
                            score[pair.verb2] += self.pmi(verb1,
                                                          pair.verb2,
                                                          entity)
                        if reverse:
                            if pair.verb2 == verb1:
                                if pair.verb1 not in events:
                                    score[pair.verb1] += self.pmi(pair.verb1,
                                                                  verb1,
                                                                  entity)

            if len(score) > 0:
                best, val = max(score.items(), key=lambda x: x[1])
                if val > 0:
                    events.append(best)
                else:
                    break
            else:
                break

        return events

    # Counts -----------------------------------------------------------------

    def count(self, verb, entity):
        return self.events.get(Event(verb=verb, entity=entity), 0)

    def cooccur(self, verb1, verb2, entity):
        return self.pairs.get(Pair(entity=entity, verb1=verb1, verb2=verb2), 0)

    # Events methods ---------------------------------------------------------

    def num_events(self, entity):
        return sum([self.events[x] for x in self.events_for(entity)])

    def events_for(self, entity):
        return [x for x in self.events.keys() if x.entity == entity]

    def num_protags(self, verb):
        return sum([self.events[x] for x in self.entities_in(verb)])

    def entities_in(self, verb):
        return [x for x in self.events.keys() if x.verb == verb]

    # Pairs methods ----------------------------------------------------------

    def num_pairs(self, entity):
        return sum([self.pairs[x] for x in self.pairs_for(entity)])

    def pairs_for(self, entity):
        return [x for x in self.pairs.keys() if x.entity == entity]

    def num_event_pairs(self, verb1, verb2):
        return sum([self.pairs[x] for x in self.pairs_involving(verb1, verb2)])

    def pairs_involving(self, verb1, verb2):
        return [x for x in self.pairs.keys()
                if x.verb1 == verb1 and x.verb2 == verb2]

    #-------------------------------------------------------------------------

    def add_filelist(self, filelist):
        """
        Extracts a set of valid narrative events from a corpus,
        groups by entity name, and returns an entity-verb(s) mapping.
        """

        if self._mode == 'token':
            aggregate = self.aggregate_tokens
        elif self._mode == 'dep':
            aggregate = self.aggregate_deps
        else:
            import sys
            sys.stderr.write(u'Warning: invalid \'mode\' argument. ' +
                             u'Doing nothing instead.\n')
            sys.stderr.flush()
            return

        for f in filelist:
            doc = corenlp.Document(f)
            for ent, verbs in aggregate(doc).items():
                nverbs = len(verbs)
                if nverbs > 1:
                    for i in range(nverbs):
                        self.events[Event(verbs[i], ent)] += 1
                        for j in range(i + 1, nverbs): 
                            self.pairs[Pair(ent, verbs[i], verbs[j])] += 1
                else:
                    self.events[Event(verbs[0], ent)] += 1

    def aggregate_tokens(self, doc, word=False):

        ent_verb_map = defaultdict(list)
        for s in doc:

            ent_cache = []
            last_verb = None

            for t in s:
                if t.pos in self.noun_tags:
                    ent = unicode(t) if word else t.lem.lower()
                    ent_cache.append(ent)
                if t.pos in self.verb_tags:
                    next_verb = unicode(t) if word else t.lem.lower()
                    for ent in ent_cache:
                        if last_verb is not None:
                            ent_verb_map[ent].extend([last_verb, next_verb])
                        else:
                            ent_verb_map[ent].append(next_verb)
                    last_verb = next_verb
                    ent_cache = []

            if len(ent_cache) > 0 and last_verb is not None:
                for ent in ent_cache:
                    ent_verb_map[ent].append(last_verb)

        return ent_verb_map

    def aggregate_deps(self, doc, word=False):
        """Extracts a set of valid narrative events from a
        document, groups by entity name, and returns an
        entity-verb(s) mapping."""

        ent_verb_map = defaultdict(list)
        for sent in doc:
            for rel in sent.deps:
                if self.valid_dep(rel):
                    ent = unicode(rel.dep) if word else rel.dep.lem.lower()
                    verb = unicode(rel.gov) if word else rel.gov.lem.lower()
                    ent_verb_map[ent].append(verb)
        return ent_verb_map

    def valid_dep(self, rel):
        if rel.type in self.relations:
            if rel.gov.pos in self.verb_tags:
                if rel.dep.pos in self.noun_tags:
                    return True
        return False

    def doc_graph(self, doc, outputfile):

        import pygraphviz as pgv
        import os
        
        if self._mode == 'token':
            aggregate = self.aggregate_tokens
        elif self._mode == 'dep':
            aggregate = self.aggregate_deps
        else:
            import sys
            sys.stderr.write(u'Warning: invalid \'mode\' argument. ' +
                             u'Doing nothing instead.\n')
            sys.stderr.flush()
            return
      
        G = pgv.AGraph(strict=False, directed=True)
        nedges = 0     
             
        for ent, verbs in aggregate(doc).items():
            if len(verbs) > 1:
                for v1, v2 in izip(verbs[:-1], verbs[1:]):
                    pmi = self.pmi(v1, v2, ent)
                    if pmi is not None:
                        edge_label = u'{}:{:2.2f}'.format(unicode(ent), pmi)
                        G.add_edge(v1, v2, label=edge_label, key=nedges)
                        nedges += 1                    
               

        outputdir = os.path.split(outputfile)[0]
        if outputdir != '' and not os.path.exists(outputdir):
            os.makedirs(outputdir)
        G.layout(prog='dot')
        G.draw(outputfile)


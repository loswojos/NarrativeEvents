import sys
from os import listdir
from os.path import isfile, join
from collections import defaultdict, namedtuple
from math import log
import corenlp as clnp
import time


Event = namedtuple("Event", ["verb", "entity"])
Pair = namedtuple("Pair", ["entity", "verb1", "verb2"])

class NarrativeBank:

    def __init__(self, filelist=None):
        self.events = defaultdict(int)
        self.pairs = defaultdict(int)
        if filelist is not None:
            self.build(filelist)

    # PMI -------------------------------------------------------------------------------

    def pmi (self, verb1, verb2, entity=None):

        if (entity):
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

        if (cooccur > 0):
            score = log (float(cooccur * num_events * num_events) / 
                            (count1 * count2 * num_pairs))
            return score * self.discount(cooccur, count1, count2)
        else:
            return None

    def discount (self, c, v1, v2):
        v = min(v1, v2)
        return ((c * v + 0.0) / ((c + 1) * (v + 1)))

    # Chain -----------------------------------------------------------------------------

    def chain (self, head, entity, size=6, reverse=False):
        events = [head]
        while len(events) < size:
            score = defaultdict(float)

            for verb1 in events:
                for pair, count in self.pairs.items():
                    if (count > 0) and (pair.entity==entity):
                        if (pair.verb1==verb1) and (pair.verb2 not in events):
                            score[pair.verb2] += self.pmi(verb1, pair.verb2, entity)
                        if (reverse) and (pair.verb2==verb1) and (pair.verb1 not in events):
                            score[pair.verb1] += self.pmi(pair.verb1, verb1, entity)

            if len(score) > 0:
                best, val = max(score.items(), key=lambda x: x[1])
                if (val > 0):
                    events.append(best)
                else:
                    break
            else:
                break

        return events

    # Counts ----------------------------------------------------------------------------

    def count (self, verb, entity):
        return self.events.get(Event(verb=verb, entity=entity), 0)

    def cooccur (self, verb1, verb2, entity):
        return self.pairs.get(Pair(entity=entity, verb1=verb1, verb2=verb2), 0)

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

    def build (self, filelist):
        """
        Extracts a set of valid narrative events from a corpus, groups by entity name,
        and returns an entity-verb(s) mapping.
        """


        for f in filelist:
            doc = clnp.Document(f)
            for ent, verbs in self.aggregate(doc).iteritems():
                if len(verbs) > 1:
                    for i in range(0, len(verbs)):
                        self.events[Event(verb=verbs[i], entity=ent)] += 1
                        for j in range(i+1, len(verbs)):
                            self.pairs[Pair(entity=ent, verb1=verbs[i], verb2=verbs[j])] += 1
                            

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

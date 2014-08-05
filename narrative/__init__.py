from collections import defaultdict, namedtuple
from math import log
import corenlp

Event = namedtuple("Event", ["verb", "entity"])
Pair = namedtuple("Pair", ["entity", "verb1", "verb2"])

class NarrativeBank:

    def __init__(self, filelist=None, mode='dep', typed=False, word=False):

        self.noun_tags = [u'NN', u'NNS', u'NNP', u'NNPS']
        self.verb_tags = [u'VB', u'VBD', u'VBG', u'VBN', u'VBP', u'VBZ']
        self.relations = [u'nsubj', u'xsubj', u'agent',
                          u'iobj', u'dobj', u'nsubjpass']

        self._mode = mode
        self._typed = typed
        self._word = word
        self.events = defaultdict(int)
        self.pairs = defaultdict(int)
        if filelist is not None:
            self.add_filelist(filelist)

    # PMI --------------------------------------------------------------------

    def pmi(self, verb1, verb2, entity=None):
        """Returns the Pointwise Mutual Information score between
        two events (verbs) given a specified protagonist. If none
        is provided, the PMI is computed corpus-wide.
        """

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
            return score * self._discount(cooccur, count1, count2)
        else:
            return None

    def _discount(self, c, v1, v2):
        v = min(v1, v2)
        return ((c * v + 0.0) / ((c + 1) * (v + 1)))

    # Chain ------------------------------------------------------------------

    def chain(self, head, entity=None, size=6, reverse=False):
        """Constructs a narrative chain given a starting head verb
        and specified protagonist. If none is provided, the chain is
        computed corpus-wide.

        - Size: indicates the maximum length of the desired chain.
        - Reverse: turns on/off bi-directionality of relations.

        Returns a list of verbs (or events) in the chain.
        """
        events = [head]
        while len(events) < size:
            score = defaultdict(float)

            for verb1 in events:
                for pair, count in self.pairs.items():
                    if pair.entity == entity or not entity:

                        if count > 0:
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

    def chain_plus(self, head, entity=None, size=6, reverse=False):
        """Constructs a narrative chain given a starting head verb
        and a specified protagonist taking into account overlapping
        arguments of verb pairs. If no protagonist is provided, the
        chain is computed corpus-wide.

        - Size: indicates the maximum length of the desired chain.
        - Reverse: turns on/off bi-directionality of relations.

        Returns a list of verbs (or events) in the chain.
        """
        events = [head]
        entities = set([x.entity.encode('utf-8') for x in self.entities_in(head)])
        while len(events) < size:
            score = defaultdict(float)

        # TODO(mw2353@gmail.com): Finish the job.

    # Counts -----------------------------------------------------------------

    def count(self, verb, entity):
        """Returns the count for an event given a protagonist"""
        return self.events.get(Event(verb=verb, entity=entity), 0)

    def cooccur(self, verb1, verb2, entity):
        """Returns the cooccurrence count of two events given a 
        protagonist
        """
        return self.pairs.get(Pair(entity=entity, verb1=verb1, verb2=verb2), 0)

    # Events methods ---------------------------------------------------------

    def num_events(self, entity):
        """Returns the number of events involving a specified
        protagonist
        """
        return sum([self.events[x] for x in self.events_for(entity)])

    def events_for(self, entity):
        """Returns all events involving a specified protagonist"""
        return [x for x in self.events.keys() if x.entity == entity]

    def num_protags(self, verb):
        """Returns the number of protagonists involved in an event"""
        return sum([self.events[x] for x in self.entities_in(verb)])

    def entities_in(self, verb):
        """Returns all protagonists involved in an event"""
        return [x for x in self.events.keys() if x.verb == verb]

    # Pairs methods ----------------------------------------------------------

    def num_pairs(self, entity):
        """Returns the number of pairs of events involving a specified 
        protagonist
        """
        return sum([self.pairs[x] for x in self.pairs_for(entity)])

    def pairs_for(self, entity):
        """Returns all pairs of events involving a specified 
        protagonist
        """
        return [x for x in self.pairs.keys() if x.entity == entity]

    def num_event_pairs(self, verb1, verb2):
        """Returns the number of pairs of events"""
        return sum([self.pairs[x] for x in self.pairs_involving(verb1, verb2)])

    def pairs_involving(self, verb1, verb2):
        """Returns all pairs of events"""
        return [x for x in self.pairs.keys()
                if x.verb1 == verb1 and x.verb2 == verb2]

    #-------------------------------------------------------------------------

    def add_filelist(self, filelist):
        """Extracts a set of valid narrative events from a corpus,
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

    def aggregate_tokens(self, doc):

        ent_verb_map = defaultdict(list)
        for sent in doc:
            ent_cache = []
            last_verb = None
            for token in sent:
                if token.pos in self.noun_tags:
                    ent = unicode(token) if self._word else token.lem.lower()
                    ent_cache.append(ent)
                if token.pos in self.verb_tags:
                    next_verb = unicode(token) if self._word else token.lem.lower()
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

    def aggregate_deps(self, doc):
        """Extracts a set of valid narrative events from a
        document, groups by entity name, and returns an
        entity-verb(s) mapping.
        """

        ent_verb_map = defaultdict(list)
        for sent in doc:
            for rel in sent.deps:
                if self.valid_dep(rel):
                    ent = self.get_mentions_head(rel.dep, doc)
                    ent = unicode(ent) if self._word else ent.lem.lower()
                    verb = unicode(rel.gov) if self._word else rel.gov.lem.lower()
                    if (self._typed):
                        if rel.type in self.relations[0:3]:
                            verb += '-subj'
                        else:
                            verb += '-obj'
                    ent_verb_map[ent].append(verb)
        return ent_verb_map

    def valid_dep(self, rel):
        """Checks if relation meets the following constraints:
            (a) Relation Type: Narrative
            (b) Governor POS: Verb
            (c) Dependent POS: Noun
        """
        if rel.type in self.relations:
            if rel.gov.pos in self.verb_tags:
                if rel.dep.pos in self.noun_tags:
                    return True
        return False

    def get_mentions_head(self, token, doc):
        """Returns the rep head of an entity coreference chain.
        """
        mentions = doc.mention_chain(token)
        return mentions.rep_head if mentions else token

    # Visualization ----------------------------------------------------------

    def nx_event_graph_for (self, entity):
        """
        """

        import networkx as nx

        graph = nx.Graph()

        for event in self.events_for(entity):
            graph.add_node(event.verb.encode('utf-8'))

        for pair in self.pairs_for(entity):
            if pair.entity == entity:
                v1 = pair.verb1.encode('utf-8')
                v2 = pair.verb2.encode('utf-8')
                score = self.pmi(v1, v2, entity)
                if score > 0:
                    graph.add_edge(v1, v2, weight=score)

        edge_labels = dict([((u,v,), '%.3g' % d['weight']) \
                        for u,v,d in graph.edges(data=True)]);
        graph.graph['edge_labels'] = edge_labels

        return graph

    # Centrality -------------------------------------------------------------

    def pagerank(self, obj, max_iter=500):

        import networkx as nx

        nx_graph = obj if type(obj) is nx.classes.graph.Graph \
                       else self.nx_event_graph_for(obj)

        return nx.pagerank(nx_graph, max_iter=max_iter)

    # Community --------------------------------------------------------------

    def louvain(self, obj):

        import community
        import networkx as nx
        
        nx_graph = obj if type(obj) is nx.classes.graph.Graph \
                       else self.nx_event_graph_for(obj)

        return community.best_partition(nx_graph)

if __name__ == "__main__":

    import sys, pickle
    from os import listdir
    from os.path import isfile, join

    # Directory containing xml files annotated by Stanford Dependency Parser
    filelist = []
    dep_dir = sys.argv[1]
    for i, path in enumerate(listdir(dep_dir)):
        if isfile(join(dep_dir, path)) and ('xml' in path):
            filelist.append(join(dep_dir, path))

    nb = NarrativeBank(filelist, typed=True)

    # Save as serialized object
    data = [nb.events, nb.pairs]
    ser_file = sys.argv[2]
    pickle.dump(data, ser_file)
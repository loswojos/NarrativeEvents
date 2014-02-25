import corenlp as cnlp
from collections import defaultdict


class NarrativeChain:

    def __init__(self, sources):

        self.co_occur = defaultdict(lambda: defaultdict(int))
        self.verb_count = defaultdict(lambda: defaultdict(int))
        self.tot_verb_count = defaultdict(int)
        self.add_sources(sources)

    def add_sources(self, sources):
        co_occur = self.co_occur
        verb_count = self.verb_count 
        tot_vcount = self.tot_verb_count

       for source in sources:    
            doc = cnlp.Document(source)

            last_verb = {}
            
            for s in doc:
                for rel in s.deps:
                    if 'VB' in rel.gov.pos and rel.dep.pos in ['NN', 'NNP', 'NNS', 'NPS']:
                        
                        ent = rel.dep.lem.lower()
                        
                        if rel.dep.lem.lower() not in last_verb:                    
                            v1 = rel.gov.lem.lower()
                            last_verb[ent] = v1
                            verb_count[ent][v1] += 1
                            tot_vcount[ent] += 1
                            
                        else:
                            v1 = last_verb[rel.dep.lem.lower()]
                            v2 = rel.gov.lem.lower()
                            verb_co_occurrence = (v1, v2) 
                                                  
                            co_occur[ent][verb_co_occurrence] += 1
                            last_verb[ent] = v2
                            verb_count[ent][v2] += 1
                            tot_vcount[ent] += 1

    def pmi(self, protag, verb1, verb2):
        return 'SOME VALUE'

 

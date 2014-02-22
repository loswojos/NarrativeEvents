import xml.etree.ElementTree as ET
from os import remove
from os.path import exists, join
from collections import defaultdict, OrderedDict
import tempfile
from subprocess import check_output
import timex

class Document:
    def __init__(self,
                 fname_or_string,
                 ssplit=True,
                 pos=True,
                 lemma=True,
                 ner=True,
                 parse=False,
                 coref=False,
                 basic_deps=False,
                 collapsed_deps=False,
                 collapsed_ccproc_deps=True,
                 size_cutoff=None,
                 timex_ne=True,
                 verbose=False):
        self.fname = None
        self.sentences = []
        self.coref = []
        self._rep_str = None

        if exists(fname_or_string):
            tree = ET.parse(fname_or_string)
        else:
            tree = ET.fromstring(fname_or_string)
        
        
        sentences = tree.findall('.//sentences/sentence')
        for i, s in enumerate(sentences):
            if not size_cutoff or i < size_cutoff:
                self.sentences.append(Sentence(s,
                                               pos=pos,
                                               lemma=lemma,
                                               ner=ner,
                                               parse=parse,
                                               basic_deps=basic_deps,
                                               collapsed_deps=collapsed_deps,
                                               collapsed_ccproc_deps=collapsed_ccproc_deps,
                                               timex_ne=timex_ne,
                                               verbose=verbose))

        if coref:
            coref_chains = tree.findall('.//coreference/coreference') 
            print len(coref_chains)
            for coref_chain in coref_chains:
                self.coref.append(CorefChain(coref_chain, self))
                
        if timex_ne:
            self.timex = OrderedDict()
            for s in self.sentences:
                for t in s:
                    if t.timex:
                        if t.timex not in self.timex:
                            self.timex[t.timex] = []
                        self.timex[t.timex].append(t)
        tree = None

    def __getitem__(self, index):
        return self.sentences[index]

    def __iter__(self):
        return iter(self.sentences)

    def __len__(self):
        return len(self.sentences)
    
    def __nonzero__(self):
        return True                        

    def __str__(self):
        if self._rep_str:
            return self._rep_str
        else:
            buf = ''
            for s in self:
                buf += str(s) + '\n' 
            self._rep_str = buf
            return self._rep_str

class CorefChain:
    def __init__(self, coref_el, doc):
        #mentions = coref_el.findall('//mention')
        self.mentions = []
        for mention in coref_el:
            
            for t in mention:
                if t.tag == 'sentence':
                    sent = int(t.text) - 1
                if t.tag == 'start':
                    start = int(t.text) - 1
                if t.tag == 'end':
                    end = int(t.text) - 1
                if t.tag == 'head':
                    head = int(t.text) - 1
            self.mentions.append(Mention(sent, start, end, head))
            doc.sentences[sent].tokens[head].coref_chain = self
        
            

class Mention:
    def __init__(self, sentence, start, end, head):
        self.sent = sentence
        self.start = start
        self.end = end
        self.head = head


class Sentence:
    def __init__(self,
                 sentence,
                 pos=True, 
                 lemma=True,
                 ner=True,
                 parse=False,
                 basic_deps=False,
                 collapsed_deps=False,
                 collapsed_ccproc_deps=True,
                 timex_ne=True,
                 verbose=False):
        self.tokens = []
        
        self.basic_deps = set() if basic_deps else None
        self.coll_deps = set() if collapsed_deps else None
        self.coll_ccp_deps = set() if collapsed_ccproc_deps else None
        
        self.deps = self.basic_deps if basic_deps else None
        self.deps = self.coll_deps if collapsed_deps else None
        self.deps = self.coll_ccp_deps if collapsed_ccproc_deps else None
        
        self._dep_graph = None

        tokens = sentence.findall('.//token')
        for token in tokens:
            word = None
            char_offset_start = None
            char_offset_end = None
            pos_tag = None
            lem = None
            ne = None
            norm_ne = None
            timex_tag = None
            for child in token:
                if child.tag == 'word':
                    word = child.text
                elif child.tag == 'CharacterOffsetBegin':
                    char_offset_start = int(child.text)
                elif child.tag == 'CharacterOffsetEnd':
                    char_offset_end = int(child.text)
                elif child.tag == 'POS' and pos:
                    pos_tag = child.text
                elif child.tag == 'lemma' and lemma:
                    lem = child.text
                elif child.tag == 'NER' and lemma:
                    ne = child.text    
                elif child.tag == 'Timex':
                    if timex_ne:
                        timex_tag = timex.make_timex(child.get('tid'), child.get('type'), child.text, verbose=verbose)
                        if timex_tag and '<{} \'{}\'>'.format(child.get('type'), child.text) != str(timex_tag):
                            import sys
                            sys.stderr.write("BAD TIMEX TAG -- DYING {} - {}\n".format(child.text, str(timex_tag)))
                            sys.stderr.flush()
                            sys.exit()
                        if not timex_tag and verbose:
                            print word, norm_ne, ' - ', child.text

                elif child.tag == 'NormalizedNER':
                    norm_ne = child.text
                elif verbose:
                    import sys
                    sys.stderr.write("Warning: Unrecognized Token('{}') " \
                                     "Property: <{}>{}</{}>".format(word,
                                                            child.tag,
                                                            child.text,
                                                            child.tag))
                    sys.stderr.flush()

            self.tokens.append(Token(word,
                                     char_offset_start,
                                     char_offset_end,
                                     pos_tag,
                                     lem,
                                     ne,
                                     norm_ne,
                                     timex_tag))
        
        parse_str = sentence.findall('.//parse')
        if parse:
            from nltk.tree import Tree
        self.parse = Tree(parse_str[0].text) if parse else None


        deps_types = sentence.findall('.//dependencies')
        for deps in deps_types:
            if deps.get('type') == 'basic-dependencies' and basic_deps:
                self._build_deps(deps, self.basic_deps)
            if deps.get('type') == 'collapsed-dependencies' and collapsed_deps:
                self._build_deps(deps, self.coll_deps)
            if deps.get('type') == 'collapsed-ccprocessed-dependencies' and collapsed_ccproc_deps:
                self._build_deps(deps, self.coll_ccp_deps)
    

    def get_dependency_graph(self):        
        if self._dep_graph:
            return self._dep_graph
        else:
            self._dep_graph = DependencyGraph(self.deps)
            return self._dep_graph

    def __iter__(self):
        return iter(self.tokens)
      
    def __getitem__(self, index):
        return self.tokens[index]      
            
    def space_sep_str(self):
        str_buff = self.tokens[0].word
        for t in self.tokens[1:]:
            str_buff += ' ' + t.word
        return str_buff

    def _build_deps(self, deps, deps_set):
                
        for dep in deps:
            
            for arg in dep:
                
                if arg.tag == 'governor':
                    gov_idx = int(arg.get('idx')) - 1
                if arg.tag == 'dependent':
                    dep_idx = int(arg.get('idx')) - 1
                    
            dtype = dep.get('type')
            deps_set.add(Dependency(dtype, gov_idx, dep_idx, self))

    def __str__(self):
        return self.space_sep_str()        
                
class Token:
    def __init__(self,
                 word,
                 char_offset_start=None,
                 char_offset_end=None,
                 pos=None,
                 lem=None,
                 ne=None,
                 norm_ne=None,
                 timex_tag=None):
        self.word = word.encode('utf-8')
        self.char_offset_start = char_offset_start
        self.char_offset_end = char_offset_end
        self.pos = pos
        self.lem = lem.encode('utf-8') if lem else None
        self.ne = ne
        self.coref_chain = None
        self.deps = []
        self.norm_ne = norm_ne
        self.timex = timex_tag

    def __str__(self):
        return self.word

class Dependency:
    def __init__(self, dtype, gov_idx, dep_idx, sentence):
        self.type = dtype
        self.gov_idx = gov_idx
        self.dep_idx = dep_idx
        if dtype == 'root':
            self.gov = Token('ROOT', lem='root')
        else:
            self.gov = sentence.tokens[gov_idx]
        self.dep = sentence.tokens[dep_idx]
        self.gov.deps.append(self)
        
        self._resolve_cycle()

    def _resolve_cycle(self):        
        #for sibling in self.gov.deps:
        for child in self.dep.deps:
            if child.dep_idx == self.gov_idx:
                if 'conj' in child.type:
                    self.dep.deps.remove(child)

    #def iterate_filtered_arcs(self, good_types):
    
    def __iter__(self):
        yield self
        token = self.dep
        for dep in sorted(token.deps, key=lambda d: d.dep_idx):
            for child in dep:
                yield child    

    def filter_iterator(self, filter_func):
        for rel in self:
            if filter_func(rel):
                yield rel 

    def __str__(self):
        return '({}:{} <- {} -- {}:{})'.format(self.dep_idx, self.dep, self.type, self.gov_idx, self.gov) 

class DependencyGraph:
    def __init__(self, deps):
        self._type = defaultdict(list)
        self._list = deps
        self.root = None 
        for dep in deps:
            if dep.type == 'root':
                self.root = dep
            self._type[dep.type].append(dep)
    #    self._build_graph(self.root)
    
    def __getitem__(self, index):
        return self._type[index]    

    def __iter__(self):
        if self.root:
            return iter(self.root)
        else:
            return iter([])

    def filter_iterator(self, filter_func):
        if self.root:
            for rel in self.root.filter_iterator(filter_func):
                yield rel
    
    def to_ipython(self):
        import pygraphviz as pgv
        G=pgv.AGraph()
        
        for dep in self._list:
            G.add_edge('{}: {}'.format(dep.gov_idx, dep.gov), '{}: {}'.format(dep.dep_idx, dep.dep), label=dep.type)

        G.layout(prog='dot')
        G.draw('/tmp/deptree.png')
        from IPython.display import Image
        return Image(filename='/tmp/deptree.png')


def annotate_list(annotators, txts, mem='2500m', threads=1, corenlp_dir=None):

    tmpfiles = []

    for txt in txts:
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.write(txt)
        tf.flush()
        tf.close
        tmpfiles.append(tf.name)
    run_pipeline(annotators,
                 tmpfiles,
                 '/tmp',
                 mem=mem,
                 threads=threads,
                 corenlp_dir=corenlp_dir)
    
    pos = True if 'pos' in annotators else False
    lemma = True if 'lemma' in annotators else False
    ner = True if 'ner' in annotators else False
    parse = True if 'parse' in annotators else False
    coref = True if 'dcoref' in annotators else False

    docs = [] 
    for tmpfile in tmpfiles:
        doc = Document('{}.xml'.format(tmpfile),
                       pos=pos,
                       lemma=lemma,
                       ner=ner,
                       parse=parse,
                       coref=coref) 
        docs.append(doc)     
    return docs
 

def annotate(annotators, txt, mem='2500m', threads=1, corenlp_dir=None):
    tf = tempfile.NamedTemporaryFile()
    tf.write(txt)
    tf.flush()
    
    if corenlp_dir == None:
        corenlp_dir = '.'
    jars = ['joda-time.jar', 'jollyday.jar', 'stanford-corenlp-1.3.5.jar',
            'stanford-corenlp-1.3.5-models.jar', 'xom.jar']
    classpath = ':'.join([join(corenlp_dir, jar) for jar in jars]) 
    pipeline = 'edu.stanford.nlp.pipeline.StanfordCoreNLP'
    cmd = 'java -Xmx{} -cp {} {} '\
          '-annotators {} -file {} '\
          '-outputDirectory {} -threads {}'.format(mem,
                                                   classpath,
                                                   pipeline,
                                                   ','.join(annotators),
                                                   tf.name,
                                                   '/tmp',
                                                   threads)
    
    check_output(cmd, shell=True)
    
    ssplit = True if 'ssplit' in annotators else False
    pos = True if 'pos' in annotators else False
    lemma = True if 'lemma' in annotators else False
    ner = True if 'ner' in annotators else False
    parse = True if 'parse' in annotators else False
    coref = True if 'dcoref' in annotators else False

    doc = Document('{}.xml'.format(tf.name),
                   ssplit=ssplit,
                   pos=pos,
                   lemma=lemma,
                   ner=ner,
                   parse=parse,
                   coref=coref) 
    tf.close()
    
    return doc

def annotate_dict(annotators,
                  a_dict,
                  mem='2500m',
                  threads=1,
                  corenlp_dir=None):

    flist = []
    fdict = {}
    for k in a_dict.keys():
        if isinstance(a_dict[k], list): 
            items = []
#or isinstance(a_dict[k], tuple) or isinstance(a_dict[k], set): 
            for txt in a_dict[k]:
                tf = tempfile.NamedTemporaryFile(delete=False)
                tf.write(txt)
                tf.flush()
                tf.close()
                items.append(tf.name)
                flist.append(tf.name)
            fdict[k] = items

    run_pipeline(annotators,
                 flist,
                 '/tmp/',
                 mem=mem,
                 threads=threads,
                 corenlp_dir=corenlp_dir)

    ssplit = True if 'ssplit' in annotators else False
    pos = True if 'pos' in annotators else False
    lemma = True if 'lemma' in annotators else False
    ner = True if 'ner' in annotators else False
    parse = True if 'parse' in annotators else False
    coref = True if 'dcoref' in annotators else False

    docmap = {}
    for k in fdict.keys():
        docs = []
        for f in fdict[k]:
            doc = Document('{}.xml'.format(f),
                           ssplit=ssplit,
                           pos=pos,
                           lemma=lemma,
                           ner=ner, 
                           parse=parse,
                           coref=coref)

            docs.append(doc)
            remove('{}.xml'.format(f))
            remove(f)
        docmap[k] = docs
        
    return docmap

def run_pipeline(annotators,
                 input_files,
                 output_dir,
                 mem='2500m',
                 threads=1,
                 corenlp_dir=None):
    flist = tempfile.NamedTemporaryFile()
    flist.write('\n'.join(input_files))
    flist.flush()

    if corenlp_dir == None:
        corenlp_dir = '.'
    jars = ['joda-time.jar', 'jollyday.jar', 'stanford-corenlp-1.3.5.jar',
            'stanford-corenlp-1.3.5-models.jar', 'xom.jar']
    classpath = ':'.join([join(corenlp_dir, jar) for jar in jars]) 
    pipeline = 'edu.stanford.nlp.pipeline.StanfordCoreNLP'
    cmd = 'java -Xmx{} -cp {} {} '\
          '-annotators {} -filelist {} '\
          '-outputDirectory {} -threads {}'.format(mem,
                                                classpath,
                                                pipeline,
                                                ','.join(annotators),
                                                flist.name, 
                                                output_dir,
                                                threads)
    check_output(cmd, shell=True)
    flist.close()


            

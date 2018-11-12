from clldutils.path import Path, remove, path_component
from segments import Tokenizer
from lingpy import *
import networkx as nx
from tqdm import tqdm
from itertools import combinations
from tabulate import tabulate

def poepy_path(*comps):
    return Path(__file__).parent.joinpath(*comps).as_posix()


class Poems(Alignments):

    def __init__(self, infile, ref='rhymeids', line='line', poem='poem',
            stanza='stanza', alignment='alignment', fuzzy=True,
            conf=poepy_path('conf', 'poems.rc'), **keywords):

        Alignments.__init__(self, infile, col=poem, row=stanza, conf=conf,
                segments=line, ref=ref, alignment=alignment, fuzzy=fuzzy,
                transcription='line_in_source')

    def stats(self):
        print('Poems:       {0}'.format(len(self.cols)))
        print('Stanzas:     {0}'.format(len(self.rows)))
        print('Lines:       {0}'.format(len(self)))
        print('Rhyme words: {0}'.format(sum([len(self.msa[self._ref][key]['ID']) for key
            in self.msa[self._ref]])))
        print('Rhymes:      {0}'.format(len(self.msa[self._ref])))
        print('Words:       {0}'.format(sum([len(self[idx, 'line'].n) for idx in
            self])))
    
    def get_rhyme_network(self, ref='rhymeids'):
        G = nx.Graph()

        for key, msa in tqdm(self.msa[ref].items()):
            for idx, seq in zip(msa['ID'], msa['seqs']):
                node = ' '.join(seq)
                try:
                    G.node[node]['weight'] += 1
                    G.node[node]['occurrences'] += [str(idx)]
                except KeyError:
                    G.add_node(node, weight=1, occurrences=[str(idx)])

            for (idxA, seqA), (idxB, seqB) in combinations(
                    zip(msa['ID'], msa['seqs']), r=2):
                nodeA, nodeB = ' '.join(seqA), ' '.join(seqB)
                try:
                    G[nodeA][nodeB]['weight'] += 1
                    G[nodeA][nodeB]['stanza'] += [self[idx, 'stanza']]
                except KeyError:
                    G.add_edge(nodeA, nodeB, weight=1, stanza=[self[idx,
                    'stanza']])
        self.G = G

    def get_connected_components(self):
        if not hasattr(self, 'G'):
            raise ValueError('compute the rhyme network first')
        self.comps = {}
        for i, comp in enumerate(nx.connected_components(self.G)):
            self.comps[i+1] = list(comp)

    def pprint(self, *stanzas):
        
        for stanza in stanzas:
            table = []
            idxs = sorted(
                    self.get_list(row=stanza, flat=True),
                    key=lambda x: self[x, 'line_order'])
            rhymeids = []
            for rhymeid in [self[idx, 'rhymeids'] for idx in idxs]:
                rhymeids += [x for x in rhymeid if x]
            rhymes = sorted(set(rhymeids), key=lambda x: rhymeids.index(x))
            for idx in idxs:
                row = [idx, ' '.join([str(x) for x in self[idx, 'line'].n])]
                for rhyme in rhymes:
                    if rhyme in self[idx, 'rhymeids']:
                        row += [self[idx, 'alignment'].n[self[idx,
                            'rhymeids'].index(rhyme)]]
                    else:
                        row += ['']
                table += [row]
            header = ['ID', 'LINE'] + ['R:{0}'.format(x) for x in rhymes]
            table = [header] + table
            print('Stanza', stanza)
            print(tabulate(table, headers='firstrow', tablefmt='pipe'))
            

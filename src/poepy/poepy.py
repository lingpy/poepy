import pathlib
import itertools

from lingpy import *
import networkx as nx
from tqdm import tqdm
from tabulate import tabulate
from lingpy.util import read_text_file
from clldutils.text import strip_chars
from lingpy.convert.html import colorRange, tokens2html
from lingpy.evaluate.acd import _get_bcubed_score, _format_results
from lingpy import log


def is_chinese(name):
    """
    Check if a symbol is a Chinese character.

    Note
    ----

    Taken from http://stackoverflow.com/questions/16441633/python-2-7-test-if-characters-in-a-string-are-all-chinese-characters
    """
    if not name:
        return False
    for ch in name:
        ordch = ord(ch)
        if not (0x3400 <= ordch <= 0x9fff) and not (0x20000 <= ordch <= 0x2ceaf) \
                and not (0xf900 <= ordch <= ordch) and not (0x2f800 <= ordch <= 0x2fa1f):
            return False
    return True


def poepy_path(*comps):
    return str(pathlib.Path(__file__).parent.joinpath(*comps))


def parse_line(line, rhymes):
    """Parse a line in the library and return the content."""
    out, alms, nline, chords = [], [], [], []
    mr = max(rhymes.values()) + 1
    for i, word in enumerate(line):
        # Check for chords in the data
        if word.count('/') > 1:
            chord, these_chords, syllables = 0, [], []
            for char in word:
                if char == '/' and chord:
                    chord -= 1
                elif char == '/':
                    these_chords += ['']
                    syllables += ['']
                    chord += 1
                elif chord and char != '/':
                    these_chords[-1] += char
                else:
                    if not syllables:
                        syllables += ['']
                        if not these_chords:
                            these_chords += ['_']
                    syllables[-1] += char

            chords += [' '.join(these_chords)]
            word = ' '.join(syllables)
        else:
            chords += ['_']

        word_ = strip_chars(',.—!?¿¡;«»', word).lower()

        if '[' in word and ']' in word:
            rhyme = word_[word_.index('[') + 1:word_.index(']')]
            word = word.replace('[' + rhyme + ']', '')
            if '/' in rhyme:
                rhyme, alm = rhyme.split('/')
                alm = alm.replace('_', ' ')
            else:
                alm = word_.replace('[' + rhyme + ']', ' ').strip()
            if rhyme not in rhymes:
                rhymes[rhyme] = mr
                mr += 1
            out += [rhymes[rhyme]]
            alms += [alm]
            nline += [word]
        else:
            out += [0]
            alms += [word_]
            nline += [word]
    return out, alms, nline, chords


def parser(filename):
    text = read_text_file(filename, normalize='NFD', lines=True)
    comment = '#'
    data = {0:
                ['poem', 'poem_number', 'stanza', 'line_in_source', 'line',
                 'line_order', 'rhymeids', 'alignment', 'refrain', 'chords']}
    meta, M = {}, {}
    number, stanza, idx, order = 0, 0, 1, 1
    atzone = False
    for line in text:
        if line.startswith('@'):
            if not atzone:
                meta = {}
            atzone = True
            meta[line[1:line.index(':')]] = line[line.index(':') + 1:].strip()
            stanza = 0
        elif not line.strip():
            stanza += 1
            order = 1
            if atzone:
                number += 1
                atzone = False
                M[meta.get('title', 'poem-{0}'.format(number))] = {
                    k: v for k, v in meta.items()}
                rhymes = {0: 0}
        elif line.startswith('[') and line.endswith(']'):
            pass
        else:
            if comment in line:
                line = line[line.index(comment):]

            refrain = ''
            if line.startswith('  '):
                refrain = 'R'
            if [x for x in line if is_chinese(x)]:
                nline, bracket = [], 0
                for char in line:
                    if is_chinese(char):
                        if bracket:
                            bracket -= 1
                            nline[-1] += char
                        else:
                            nline += [char]
                    else:
                        if char == '[':
                            bracket += 1
                            nline += ['']
                        nline[-1] += char
            else:
                nline = line.strip().split()
            rhymeids, alignment, nline, chords = parse_line(nline, rhymes)
            data[idx] = [
                meta.get('title', 'poem-{0}'.format(number)),
                str(number),
                '{0}.{1}'.format(number, stanza),
                line,
                ' + '.join(nline),
                order,
                rhymeids,
                ' + '.join(alignment),
                refrain,
                chords
            ]
            idx += 1
            order += 1
    poe = Poems(data)
    poe._meta['poems'] = M
    return poe


class Poems(Alignments):
    def __init__(self, infile, ref='rhymeids', line='line', poem='poem',
                 stanza='stanza', alignment='alignment',
                 line_in_source='line_in_source',
                 conf=poepy_path('conf', 'poems.rc'), **keywords):

        self._stanza = stanza
        self._ref = ref
        self._line = line
        self._poem = poem
        self._alignment = alignment
        self._mode = 'fuzzy'
        self._transcription = line_in_source

        Alignments.__init__(self, infile, col=poem, row=stanza, conf=conf,
                            segments=line, ref=ref, alignment=alignment, fuzzy=True,
                            transcription=line_in_source, split_on_tones=False)

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

            for (idxA, seqA), (idxB, seqB) in itertools.combinations(
                    zip(msa['ID'], msa['seqs']), r=2):
                nodeA, nodeB = ' '.join(seqA), ' '.join(seqB)
                try:
                    G[nodeA][nodeB]['weight'] += 1
                    G[nodeA][nodeB]['stanza'] += [self[idx, 'stanza']]
                except KeyError:
                    G.add_edge(nodeA, nodeB, weight=1, stanza=[self[idx,
                                                                    'stanza']])
        self.G = G

    def naive_rhyme_detection(self, stanzas, threshold=0.5):

        if stanzas[0] == '*':
            stanzas = self.rows
        for stanza in stanzas:
            idxs = sorted(self.get_list(row=stanza, flat=True), key=lambda x:
            self[x, 'line_order'])
            matrix = [[0 for x in idxs] for y in idxs]
            for (i, idxA), (j, idxB) in itertools.combinations(enumerate(idxs), r=2):
                matrix[i][j] = matrix[j][i] = edit_dist(
                    self[idxA, self._line],
                    self[idxB, self._line],
                    distance=True)

    def get_connected_components(self):
        if not hasattr(self, 'G'):
            raise ValueError('compute the rhyme network first')
        self.comps = {}
        for i, comp in enumerate(nx.connected_components(self.G)):
            self.comps[i + 1] = list(comp)

    def pprint(self, *stanzas, chords=False, tablefmt='pipe'):
        rhymeids = []
        if stanzas[0] == '*': stanzas = self.rows
        for stanza in stanzas:
            idxs = sorted(
                self.get_list(row=stanza, flat=True),
                key=lambda x: self[x, 'line_order']
            )
            for rhymeid in [self[idx, 'rhymeids'] for idx in idxs]:
                rhymeids += [x for x in rhymeid if x]
        rhymes = sorted(set(rhymeids), key=lambda x: rhymeids.index(x))
        table = []
        for stanza in stanzas:
            idxs = sorted(
                self.get_list(row=stanza, flat=True),
                key=lambda x: self[x, 'line_order'])
            for idx in idxs:
                if chords:
                    ctext = []
                    for i, (word, chord) in enumerate(zip(self[idx, 'line'].n, self[idx,
                                                                                    'chords'])):
                        if self[idx, 'rhymeids'][i]:
                            if len(chord.split()) > 1:
                                rhyming = 1
                            else:
                                rhyming = 2
                        else:
                            rhyming = 0
                        ctext += [[]]
                        for syllable, schord in zip(word, chord.split()):
                            fmt = '{0:' + str(len(str(syllable)) + rhyming) + '}'
                            ctext[-1] += [fmt.format(schord).replace('_', ' ')]
                        ctext[-1] = ' '.join(ctext[-1])
                    table += [['', '', ' '.join(ctext)]]

                row = []
                line = [str(x) for x in self[idx, 'line'].n]
                for rhyme in rhymes:
                    if rhyme in self[idx, 'rhymeids']:
                        row += [[]]
                        for i, rhymeid in enumerate(self[idx, 'rhymeids']):
                            if rhymeid == rhyme:
                                row[-1] += [self[idx, 'alignment'].n[i]]
                                line[i] = '*' + line[i] + '*'
                        row[-1] = ' / '.join([str(x) for x in row[-1]])
                    else:
                        row += ['']
                table += [[idx, stanza, ' '.join(line)] + row]
            table += [len(table[-1]) * ['']]

        header = ['ID', 'STANZA', 'LINE'] + ['R:{0}'.format(x) for x in rhymes]
        table = [header] + table[:-1]
        print(tabulate(table, headers='firstrow', tablefmt=tablefmt))

    def songbook(self, *poems, filename='poems.tex'):
        """Export songs to latex songbook"""

        text = ""
        meta = self._meta.get('poems', {})
        if poems[0] == '*':
            poems = self.cols
        for poem in poems:
            log.info('analyzing poem' + poem)
            idxs = sorted(self.get_list(col=poem, flat=True),
                          key=lambda x: (self[x, 'stanza'], self[x, 'line_order']))
            text += r'\begin{{song}}{{{title}}}{{}}{{}}{{{author}}}{{}}{{}}'.format(
                title=meta.get(poem, {}).get('title'),
                author=meta.get(poem, {}).get('author')) + '\n'
            stanza, before = '', ''
            for idx in idxs:
                new_stanza, refrain = self[idx, 'stanza'], self[idx, 'refrain']
                if new_stanza != stanza:

                    if before == 'verse':
                        text += r'\end{SBVerse}' + '\n'
                    elif before == 'refrain':
                        text += r'\end{SBChorus}' + '\n'
                    if refrain:
                        text += r'\begin{SBChorus}' + '\n'
                        before = 'refrain'
                    else:
                        before = 'verse'
                        text += r'\begin{SBVerse}' + '\n'
                    stanza = new_stanza
                line = []
                for word, chords in zip(self[idx, 'line'].n, self[idx, 'chords']):
                    small_line = []
                    for syl, chord in zip(word, chords.split()):
                        syl = syl.replace('_', ' ')
                        if chord.strip('_').strip():
                            small_line += [r'\Ch{' + chord + '}{' + syl + '}']
                        else:
                            small_line += [syl]
                    line += ['-'.join(small_line)]
                text += ' '.join(line) + '\n\n'
            if refrain:
                text += r'\end{SBChorus}' + '\n'
            else:
                text += r'\end{SBVerse}' + '\n'
            text += r'\end{song}' + '\n\n'
        pathlib.Path(filename).write_text(text, encoding='utf8')
        log.info('wrote file {0}'.format(filename))

    def html(self, *stanzas, filename='output.html', alignment=False,
             chords=False):
        rhymeids = []
        if stanzas[0] == '*': stanzas = self.rows
        for stanza in stanzas:
            idxs = sorted(
                self.get_list(row=stanza, flat=True),
                key=lambda x: self[x, 'line_order']
            )
            for rhymeid in [self[idx, 'rhymeids'] for idx in idxs]:
                rhymeids += [x for x in rhymeid if x]

        rhymes = sorted(set(rhymeids), key=lambda x: rhymeids.index(x))
        colors_ = colorRange(len(rhymes) + 5)
        colors = []
        for i, (a, b) in enumerate(zip(colors_, colors_[::-1])):
            if i % 2:
                colors += [a]
            else:
                colors += [b]

        table = []
        for stanza in stanzas:
            idxs = sorted(
                self.get_list(row=stanza, flat=True),
                key=lambda x: self[x, 'line_order'])
            for idx in idxs:
                if chords:
                    table += [['<span>{0}</span>'.format(
                        chord) for chord in self[idx, 'chords']]]
                row = []
                line = [str(x) for x in self[idx, 'line'].n]
                for color, rhyme in zip(colors, rhymes):
                    if rhyme in self[idx, 'rhymeids']:
                        row += [[]]
                        for i, rhymeid in enumerate(self[idx, 'rhymeids']):
                            if rhymeid == rhyme:
                                row[-1] += [tokens2html(self[idx,
                                                             'alignment'].n[i])]
                                line[i] = '<span style="color:white;background-color:{0};font-weight:bold;">'.format(
                                    color) + line[i] + '</span>'
                        row[-1] = ' '.join([str(x) for x in row[-1]])
                    else:
                        row += ['']

                table += [[idx, stanza, ' '.join(line)]]
                if alignment:
                    table[-1] += row
            table += [len(table[-1]) * ['<span style="color:white">.</span>']]

        header = ['ID', 'STANZA', 'LINE']
        if alignment: header += ['R:{0}'.format(x) for x in rhymes]

        table = [header] + table[:-1]
        with open(filename, 'w') as f:
            f.write('<html><head><meta http-equiv="content-type"'
                    ' content="text/html; charset=utf-8" /></head>')
            f.write('<body>' + tabulate(table, tablefmt='html') + '</body></html>')

    def compare(self, other, *stanzas):

        p, r, f, count, hits, missed = [], [], [], 0, 0, 0
        diffs = []
        if stanzas[0] == '*':
            stanzas = self.rows
        for stanza in stanzas:
            if not stanza in other.rows:
                missed += 1
            else:
                idxsA = sorted(self.get_list(row=stanza, flat=True),
                               key=lambda x: self[x, 'line_order'])
                idxsB = sorted(other.get_list(row=stanza, flat=True),
                               key=lambda x: other[x, 'line_order'])
                if len(idxsA) == len(idxsB):
                    count += 1
                    rhymesA, dictA, cogid = [], {}, 1
                    for idx in idxsA:
                        rhymeids = self[idx, 'rhymeids']
                        found = False
                        for rhymeid in rhymeids:
                            if rhymeid:
                                if rhymeid not in dictA:
                                    dictA[rhymeid] = cogid
                                    cogid += 1
                                rhymesA += [dictA[rhymeid]]
                                found = True
                                break
                        if not found:
                            rhymesA += [cogid]
                            cogid += 1

                    rhymesB, dictB, cogid = [], {}, 1
                    for idx in idxsB:
                        rhymeids = other[idx, 'rhymeids']
                        found = False
                        for rhymeid in rhymeids:
                            if rhymeid:
                                if rhymeid not in dictB:
                                    dictB[rhymeid] = cogid
                                    cogid += 1
                                rhymesB += [dictB[rhymeid]]
                                found = True
                                break
                        if not found:
                            rhymesB += [cogid]
                            cogid += 1
                    if rhymesA == rhymesB:
                        hits += 1

                    if len(rhymesA) == len(rhymesB) and rhymesA:
                        p += [_get_bcubed_score(rhymesA, rhymesB)]
                        r += [_get_bcubed_score(rhymesB, rhymesA)]
                        f += [2 * (p[-1] * r[-1]) / (p[-1] + r[-1])]
                        if f[-1] != 1:
                            diffs += [stanza]
                    else:
                        print(rhymesA)
                        print(rhymesB)
                        print('---', stanza, '---')
        print(hits / count, hits, count)
        print(_format_results(
            'bcubes',
            sum(p) / len(p),
            sum(r) / len(r),
            sum(f) / len(f)))
        print(len(p), self.height, other.height)
        return diffs

    def text(self, filename, poem):

        base = ''
        idxs = self.get_list(col=poem)
        for key, val in self._meta['poems'][poem].items():
            base += '@' + key.upper() + ': ' + val + '\n'

        _rhymes = 'abcdefghijklmnopqrstuvwxyz'
        rhymes = list(_rhymes)
        rhymes += list(_rhymes.upper())
        rhymes += [a + a for a in _rhymes]
        rhymes += [a + a for a in _rhymes.upper()]
        rhymes += [a + a + a for a in _rhymes]
        rhymes += [a + a + a for a in _rhymes.upper()]

        rhymeids = sorted(self.get_etymdict(ref='rhymeids'))[1:]

        stanza = ''
        for idx in idxs:
            line = ''
            current_stanza = self[idx, 'stanza']
            if current_stanza != stanza:
                stanza = current_stanza
                base += '\n'
            for i, (word, rhyme) in enumerate(zip(
                    self[idx, 'line'].n,
                    self[idx, 'rhymeids'])):
                if rhyme:
                    # get the rhyme number
                    try:
                        rhyme = rhymes[rhymeids.index(rhyme)]
                    except IndexError:
                        rhyme = str(rhyme)
                    rhyme = '[' + rhyme + ']'
                else:
                    rhyme = ''
                line += ' ' + rhyme + str(word)
            if self[idx, 'refrain']:
                line = ' ' + line + '\n'
            else:
                line = line.strip() + '\n'
            base += line
        with open(filename, 'w') as f:
            f.write(base)

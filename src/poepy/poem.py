"""
Parser for basic poetry format.
"""
from collections import OrderedDict
from poepy.data import STOPS


def parse_word(text, stops=STOPS):
    """Extract rhyme information from one word."""
    in_bracket, in_phonetic = False, False
    words, rhymes, sounds = [], [], []
    for char in text:
        if char == '[':
            in_bracket = True
            rhymes += ['']
            words += ['']
            sounds += ['']
        elif char == ']':
            in_bracket = False
            in_phonetic = False
        else:
            if in_bracket:
                if char == '/':
                    in_phonetic = True
                elif not in_phonetic:
                    rhymes[-1] += char
                else:
                    sounds[-1] += char
            else:
                if char in stops:
                    pass
                elif not words:
                    words += [char]
                    rhymes += ['']
                    sounds += ['']
                else:
                    words[-1] += char
                    
    return words, rhymes, sounds


def parse_line(text, stops=STOPS):
    """
    Parse a line for each word and return the data in analyzed form.
    """
    original, no_rhymes, phonetic, rhymes = [], [], [], []
    refrain = False
    if text.startswith('  '):
        refrain = True
        text = text.strip()

    for word in text.split():
        w, r, s = parse_word(word, stops=stops)
        original += [word]
        no_rhymes += [w]
        phonetic += [s]
        rhymes += [r]
    return text, original, no_rhymes, phonetic, rhymes, refrain

class Poem(object):

    def __init__(self, meta, stanzas, **kw):
        self.meta = meta
        self.stanzas = stanzas
        for key in ['author', 'year', 'title']:
            if key not in self.meta:
                self.meta[key] = 'unknown'

    @property
    def author(self):
        return self.meta['author']

    @property
    def year(self):
        return self.meta['year']

    @property
    def title(self):
        return self.meta['title']


    @classmethod
    def from_text(cls, text, **kw):
        """
        Create a poem from text.
        """
        meta = {}
        stanzas = OrderedDict()
        current_stanza = 0
        stanzas_in_order = []
        line_number = 0
        for line in text.splitlines():
            if line.startswith('@') and ':' in line:
                meta[line[1:line.index(':')].lower()] = line[line.index(':')+1:].strip()
            elif not line.strip():
                current_stanza += 1
            elif line.strip() and current_stanza:
                if not current_stanza in stanzas:
                    stanzas[current_stanza] = OrderedDict()
                    line_number = 1
                else:
                    line_number += 1
                parsed = parse_line(line)
                stanzas[current_stanza][line_number] = {
                        'original_text': parsed[0],
                        'original_words': parsed[1],
                        'words': parsed[2],
                        'rhymes': parsed[3],
                        'sounds': parsed[4],
                        'refrain': parsed[5]}
        return cls(meta, stanzas)




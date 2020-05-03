import pytest
from poepy.poem import *

def test_parse_word():
    w, r, s = parse_word('[a]apfel[abc/blyten]lüten!')
    assert r[0] == 'a'
    assert r[1] == 'abc'
    assert w[0] == 'apfel'
    assert w[1] == 'lüten'
    assert s[1] == 'blyten'

    parsed = parse_line('  es schienen so golden die [a/ʃtɛrnə]Sterne,')
    assert parsed[-1]
    assert parsed[0] == 'es schienen so golden die [a/ʃtɛrnə]Sterne,'
    assert parsed[1][-1].endswith('Sterne,')
    assert parsed[2][-1][0] == 'Sterne'
    assert parsed[3][-1][0] == 'ʃtɛrnə'
    assert parsed[4][-1][0] == 'a'

    poem = Poem.from_text(
        "@title: Sterne\n"
        "@author: Tester\n"
        "@freizeit: no\n\n"
        "Es schienen so golden die [a]Sterne,\n"
        "Am Fenster ich einsam [b]stand.\n"
        "Und sah wie in weiter [a]Ferne.\n"
        "Der Ball im Tore ver[b]schwand.\n")

    assert poem.title == 'Sterne'
    assert poem.author == 'Tester'
    assert poem.meta['freizeit'] == 'no'
    assert poem.year == 'unknown'


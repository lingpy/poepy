from poepy import Poems
from poepy.poepy import poepy_path


def test_Poems(tmpdir, capsys):
    poe = Poems(poepy_path('data', 'Wang1980.tsv'))
    poe.stats()
    out, _ = capsys.readouterr()
    assert 'Stanzas' in out
    #assert poe.songbook('*', filename=str(tmpdir.join('test.tex')))
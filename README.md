# PoePy: A Python library for handling annotated rhymes.

Usage example, retrieve a set of poems and calculate initial statistics:

```python
>>> from poepy import *
>>> poe = Poems(poepy_path('data', 'Wang1980.tsv'))
>>> poe.stats()
Poems:       295
Stanzas:     1180
Lines:       7285
Rhyme words: 5271
Rhymes:      1746
Words:       29503
```

Compare two collections of poems for rhyme annotations:

```python
>>> from poepy import *
>>> poe1 = Poems(poepy_path('data', 'Wang1980.tsv'))
>>> poe2 = Poems(poepy_path('data', 'Baxter1992.tsv'))
>>> diffs = poe1.compare(poe2, '*')
0.8364485981308412 895 1070
*************************
* bcubes -Scores        *
* --------------------- *
* Precision:     0.9855 *
* Recall:        0.9666 *
* F-Scores:      0.9715 *
*************************'
1070 1142 1180
```

# wikimark -- get a sens of it

**work in progress**

wikimark goal is to give you an idea of what the text is about.

# What?

Given a text it return dictionary made of wikipedia categories, e.g.:

```python
out = wikimark("""Peter Hintjens wrote about the relation between technology and culture.
Without using a scientifical tone of state-of-the-art review of the anthroposcene antropology,
he gives a fair amount of food for thought. According to Hintjens, technology is doomed to
become cheap. As matter of fact, intelligence tools will become more and more accessible which
will trigger a revolution to rebalance forces in society.""")

for category, score in wikimark:
    print('{} ~ {}'.format(category, score))
```

The above program will output something like that:

```python
Art ~ 0.2
Science ~ 0.8
Society ~ 0.4
```

# Getting started

```bash
$ mkdir build
$ wikimark.py collect build
$ wikimark.py process build
$ wikimark.py guess build https://en.wikipedia.org/wiki/Age_of_Enlightenment
similarity
 +-- People ~ 0.12902167949936127
 |   +-- Philosophers and social scientists ~ 0.16458384919191754
 |   +-- Politicians and leaders ~ 0.16346975675057948
 |   +-- Writers ~ 0.15173445927365872
 |   +-- Inventors and scientists ~ 0.14769159440526514
 |   +-- Religious figures ~ 0.12113421575199218
 |   +-- Composers and musicians ~ 0.11898056150234657
 |   +-- Mathematicians ~ 0.11649194579749912
 |   +-- Explorers ~ 0.11333111580763379
 |   +-- Artists ~ 0.11108819466279556
 |   +-- Filmmakers ~ 0.1085489290755553
 |   +-- Businessmen ~ 0.10218385227373053
 +-- Society and social sciences ~ 0.11801960771701694
 |   +-- General ~ 0.13976274021971652
 |   +-- Politics and government ~ 0.13498894108434512
 |   +-- Social issues ~ 0.12584918906141762
 |   +-- Media ~ 0.11645370523758253
 |   +-- Psychology ~ 0.10482146591566212
 |   +-- Business and economics ~ 0.10408332370167317
 |   +-- Language ~ 0.10017788879872162
 +-- Health and medicine ~ 0.11002660871018206
 |   +-- Illness ~ 0.1184546818737691
 |   +-- Health and fitness ~ 0.10665187381970996
 |   +-- Pharmaceuticals ~ 0.10497327043706711
 +-- Science ~ 0.10804459357616268
 |   +-- Astronomy ~ 0.11993846155973248
 |   +-- Biology ~ 0.11390819225006284
 |   +-- Physics ~ 0.11294825655190031
 |   +-- General ~ 0.10121826398511151
 |   +-- Earth science ~ 0.10038764600059467
 |   +-- Chemistry ~ 0.09986674110957425
 +-- Technology ~ 0.08941836214353431
 |   +-- Food, agriculture and health ~ 0.11142273843823869
 |   +-- Navigation and timekeeping ~ 0.10746503544603578
 |   +-- Materials ~ 0.10672329087520042
 |   +-- Energy ~ 0.10654532297855818
 |   +-- Optical ~ 0.10582936318945477
 |   +-- Space ~ 0.10471176046898041
 |   +-- Media and communication ~ 0.10426551244432618
 |   +-- Tools and machinery ~ 0.10245302067015787
 |   +-- Structural engineering ~ 0.1017269236619739
 |   +-- Computing and information technology ~ 0.1011999542208403
 |   +-- Electronics ~ 0.10031248099884797
 |   +-- Weapons ~ 0.09920166661686595
 |   +-- Transportation ~ 0.0
 |   +-- General ~ 0.0
 +-- Everyday life ~ 0.08119157295492874
 |   +-- General ~ 0.10303037342207341
 |   +-- Sexuality and gender ~ 0.10182983306851541
 |   +-- Family and kinship ~ 0.10140725724569735
 |   +-- Recreation and entertainment ~ 0.0996904010383575
 |   +-- Food and drink ~ 0.0
 +-- Philosophy and religion ~ 0.07971456632289997
 |   +-- Specific religions ~ 0.12005233754891315
 |   +-- Religion ~ 0.11909136141978678
 |   +-- Philosophy ~ 0.0
 +-- Arts and culture ~ 0.06859538492547092
 |   +-- Artistic movements ~ 0.15214185026125848
 |   +-- Literature ~ 0.11322450658495442
 |   +-- General ~ 0.11139517673333715
 |   +-- Music ~ 0.10340616089874635
 |   +-- Visual arts ~ 0.0
 |   +-- Architecture ~ 0.0
 |   +-- Performing arts ~ 0.0
 +-- History ~ 0.0641463552907817
 |   +-- History by region ~ 0.12432503127623418
 |   +-- History by subject matter ~ 0.1213295034017715
 |   +-- Ancient history ~ 0.10294025184172263
 |   +-- General ~ 0.1004297005157437
 |   +-- Post-classical history ~ 0.0
 |   +-- Modern history ~ 0.0
 |   +-- Prehistory ~ 0.0
 +-- Geography ~ 0.052371487656021676
     +-- Terrestrial features ~ 0.10553500968472539
     +-- Hydrologic features ~ 0.10459033102272292
     +-- Continents and regions ~ 0.10410358522868174
     +-- Cities ~ 0.0
     +-- General ~ 0.0
     +-- Countries ~ 0.0
```

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

for category, score in out:
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
$ pipenv shell
$ pipenv install
$ mkdir build
$ wikimark.py collect build
$ wikimark.py process build
$ ./wikimark.py guess build/ https://en.wikipedia.org/wiki/Personal_knowledge_base
similarity
 +-- Technology ~ 0.17140869732263997
 |   +-- Computing and information technology ~ 0.17140869732263997
 +-- Science ~ 0.15282761155955393
 |   +-- Physics ~ 0.15282761155955393
 +-- Society and social sciences ~ 0.1509537790911352
 |   +-- Media ~ 0.18972681220299564
 |   +-- Language ~ 0.13639047880005872
 |   +-- Social issues ~ 0.12674404627035118
 +-- People ~ 0.13834670265555754
 |   +-- Politicians and leaders ~ 0.14120826187649851
 |   +-- Inventors and scientists ~ 0.1354851434346166
 +-- Everyday life ~ 0.13576029816193244
 |   +-- Recreation and entertainment ~ 0.13576029816193244
 +-- Arts and culture ~ 0.12927331950583784
 |   +-- Literature ~ 0.12927331950583784
 +-- History ~ 0.12506135377632388
     +-- General ~ 0.12506135377632388
$ ./wikimark.py guess build/ https://en.wikipedia.org/wiki/Age_of_Enlightenment
similarity
 +-- People ~ 0.15687219491239904
 |   +-- Philosophers and social scientists ~ 0.16457852199543446
 |   +-- Politicians and leaders ~ 0.16347889387078907
 |   +-- Writers ~ 0.1517315759601271
 |   +-- Inventors and scientists ~ 0.14769978782324555
 +-- Arts and culture ~ 0.15212829109952172
 |   +-- Artistic movements ~ 0.15212829109952172
 +-- Society and social sciences ~ 0.13352365637215666
 |   +-- General ~ 0.13973604120782718
 |   +-- Politics and government ~ 0.13498417545798852
 |   +-- Social issues ~ 0.12585075245065422
 +-- History ~ 0.1228191269614678
     +-- History by region ~ 0.12432311591982381
     +-- History by subject matter ~ 0.12131513800311178
```

You can also use your own corpus.

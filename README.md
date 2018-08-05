# wikimark -- get a sens of it

wikimark goal is to give you an idea of what the text is about.

**It's not evaluated. It gives sensible results but I am not sure it's
the right approach**

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

That is the goal of the project but were are not there yet or are we
pushing forward the final frontier.

# Getting started

## Detecting language

To get started we will use the algorithm to detect language:

```bash
$ pipenv shell
$ pipenv install --dev
$ ./wikimark.py process data/
$ curl https://fr.wikipedia.org/wiki/Science | ./wikimark.py guess data/
```

Here is the output:

```bash
(sensimark-P02TGHgF) amirouche@ubujul18:~/src/python/sensimark$ curl https://fr.wikipedia.org/wiki/Science | ./wikimark.py guess data/
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  609k  100  609k    0     0   743k      0 --:--:-- --:--:-- --:--:--  742k
similarity
 +-- wikipedia ~ 0.4999974735532797
     +-- french ~ 0.9002363895619202
     +-- english ~ 0.09975855754463928
```

## Detecting Category and Sub-Category

Based Wikipedia Vital Articles Level 3 Categories and Sub-Categories.

```bash
$ pipenv shell
$ pipenv install  --dev
$ mkdir build
$ wikimark.py collect build
$ wikimark.py process build
$ curl https://github.com/cultureandempire/cultureandempire.github.io/blob/master/culture.md | ./wikimark.py guess build/
similarity
 +-- Technology ~ 0.09932770275501317
 |   +-- General ~ 0.09932770275501317
 +-- Science ~ 0.09905069171042175
 |   +-- General ~ 0.09905069171042175
 +-- Geography ~ 0.09897996204391411
 |   +-- Continents and regions ~ 0.09914627336640339
 |   +-- General ~ 0.09881365072142484
 +-- Mathematics ~ 0.09897542847422805
 |   +-- Other ~ 0.09911568655298664
 |   +-- Arithmetic ~ 0.09883517039546945
 +-- Society and social sciences ~ 0.09886767613461538
 |   +-- Social issues ~ 0.09886767613461538
 +-- History ~ 0.09886377525104235
     +-- General ~ 0.09893293240770612
     +-- History by subject matter ~ 0.09884456012696491
     +-- Post-classical history ~ 0.09881383321845605
$ curl https://en.wikipedia.org/wiki/Personal_knowledge_base | ./wikimark.py guess build
similarity
 +-- Mathematics ~ 0.0993756246619002
 |   +-- Other ~ 0.09944645420034719
 |   +-- Arithmetic ~ 0.0993047951234532
 +-- History ~ 0.09932122839459406
 |   +-- Post-classical history ~ 0.09939344609873874
 |   +-- History by subject matter ~ 0.0992490106904494
 +-- Technology ~ 0.09930023484792067
 |   +-- Computing and information technology ~ 0.09940246773954364
 |   +-- General ~ 0.09919800195629769
 +-- Geography ~ 0.099271977035576
 |   +-- General ~ 0.09935064012068967
 |   +-- Continents and regions ~ 0.09919331395046231
 +-- Society and social sciences ~ 0.09916934772113263
     +-- General ~ 0.09918826756048632
     +-- Social issues ~ 0.09915042788177894
$ curl https://en.wikipedia.org/wiki/Age_of_Enlightenment | ./wikimark.py guess build
similarity
 +-- History ~ 0.09939241274306507
 |   +-- Modern history ~ 0.10042636927477488
 |   +-- History by subject matter ~ 0.09930107973217772
 |   +-- History by region ~ 0.09911410256819446
 |   +-- General ~ 0.0987280993971132
 +-- Geography ~ 0.09891518376351204
 |   +-- Continents and regions ~ 0.0989354199303044
 |   +-- General ~ 0.09889494759671967
 +-- Science ~ 0.09889482066567144
 |   +-- General ~ 0.09889482066567144
 +-- Technology ~ 0.09871997655793871
 |   +-- General ~ 0.09871997655793871
 +-- People ~ 0.09870483339781669
 |   +-- Mathematicians ~ 0.09870483339781669
 +-- Arts and culture ~ 0.09867058277473856
     +-- Literature ~ 0.09867058277473856
```

You can also use your own corpus.

# How?

wikimark use [gensim](https://radimrehurek.com/gensim/)
and [scikit-learn](https://scikit-learn.org/).

- A Doc2Vec embedding is built with the whole corpus.
- Regression models for each subcategory is built using the Doc2Vec
  embedding of the related paragraphs of each documents using
  1-vs-other strategy.

The `wikimark.py guess` command will predict the score of the input
document against each subcategory regression models.

# Who?

[Amirouche](mailto:amirouche@hypermove.net)

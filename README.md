# wikimark -- get a sens of it

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

TBD

# CLI

```
curl https://content.cultureandempire.com/chapter2.html | wikimark
```

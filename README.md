# sensimark -- get a sense of it

sensimark goal is to give you an idea of what the text is about.


# What?

Given a text it return dictionary made of wikipedia categories, e.g.:

```
$ $ curl https://github.com/amirouche/sensimark | python wikimark.py v3 estimate level3/
```

The above program will output something like that:

```python
sensimark/level3/Health, medicine and disease  ~  -1.2806567221295668
sensimark/level3/Arts  ~  -1.0704664829367938
sensimark/level3/Everyday life  ~  -0.8661099064382237
sensimark/level3/Geography  ~  -0.7565684475124224
sensimark/level3/Mathematics  ~  -0.5093076598042084
sensimark/level3/History  ~  -0.46668539628320677
sensimark/level3/Philosophy and religion  ~  0.06943753800317543
sensimark/level3/Society and social sciences  ~  0.8778890366427974
sensimark/level3/People  ~  0.8894349729047532
sensimark/level3/Science  ~  1.5233850644220377
sensimark/level3/Technology  ~  1.5896480031316587
```

# Getting started

```
$ git clone https://github.com/amirouche/sensimark
$ cd sensimark && pipenv install --dev && pipenv shell
$ python -m spacy download en_core_web_lg
$ python wikimark.py v3 train level3/
```

Then run something like the following:

```
$ curl https://hintjens.gitbooks.io/culture-empire/content/chapter6.html | python wikimark.py v3 estimate level3/

sensimark/level3/Arts  ~  -1.2370657629033888
sensimark/level3/Health, medicine and disease  ~  -1.061391644389691
sensimark/level3/Mathematics  ~  -0.8448657596048442
sensimark/level3/Everyday life  ~  -0.3054167581524906
sensimark/level3/History  ~  -0.25864448035539783
sensimark/level3/Philosophy and religion  ~  -0.10844689359787853
sensimark/level3/People  ~  -0.07366867356878538
sensimark/level3/Geography  ~  0.08083613643794024
sensimark/level3/Science  ~  0.17233510277604044
sensimark/level3/Technology  ~  1.1840206286289219
sensimark/level3/Society and social sciences  ~  2.452308104729575
```

# How?

- First, Infer vectors from paragraph extracted from html with spacy
- Then, do a regression using scikit-learn's `SGDRegressor` again each
  category.
- Eventually, predict the probability that new documents fit into the categories

# Who?

[Amirouche](mailto:amirouche@hyper.dev)

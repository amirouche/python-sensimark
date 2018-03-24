#!/usr/bin/env python3
"""Usage:
  wikimark.py collect OUTPUT
  wikimark.py process INPUT
  wikimark.py guess INPUT URL
"""
import json
import re
from pathlib import Path
from string import punctuation

import requests

from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import Doc2Vec
from lxml import html
from lxml.html.clean import clean_html
from docopt import docopt

REST_API = 'https://en.wikipedia.org/api/rest_v1/page/html/'
INPUT = REST_API + 'Wikipedia%3AVital_articles'


REGEX_TITLE = re.compile(r'[^(]+')


def tokenize(string):
    text = clean_html(html.fromstring(string)).text_content()
    clean = ''.join([' ' if c in punctuation else c for c in text]).split()
    tokens = [e for e in (' '.join(clean)).lower().split() if len(e) > 2]
    return tokens


def get_children(xml):
    """List children ignoring comments"""
    return [e for e in xml.iterchildren() if not isinstance(e, html.HtmlComment)]  # noqa


def extract_subcategory(section):
    out = dict()
    children = get_children(section)
    # ignore some div at the end, that happens in Geography > General
    header, ul = children[0], children[1]
    title = header.xpath('./text()')[0]
    title = REGEX_TITLE.match(title).group().strip()
    out['title'] = title
    out['articles'] = list()
    for href in ul.xpath('./li/a/@href'):
        href = href[2:]
        if href not in ("Wikipedia:Vital_articles/Level/2", "Wikipedia:Vital_articles/Level/1"):  # noqa
            out['articles'].append(href)
    return out


def extract_category(section):
    out = dict()
    header, div = get_children(section)
    title = header.xpath('./text()')[0]
    title = REGEX_TITLE.match(title).group().strip()
    out['title'] = title
    out['subcategories'] = list()
    for h3 in div.xpath('.//h3'):
        # for mathematics, the above xpath doesn't work skip it, see
        # the talk page for more info
        section = h3.getparent()
        subcategory = extract_subcategory(section)
        out['subcategories'].append(subcategory)
    return out


def get_specification():
    """Get vital categories with references to the articles

    It returns a dict of dict"""
    response = requests.get(INPUT)
    xml = html.fromstring(response.text)
    section = xml.xpath('body/section[@data-mw-section-id=1]')[0]
    children = get_children(section)
    assert len(children) == 14, "the html changed, update the code"
    sections = children[3:]
    categories = [extract_category(section) for section in sections]
    return categories


def collect(output):
    specification = get_specification()
    output = Path(output)
    # write specification
    with (output / 'specification.json').open('w') as f:
        f.write(json.dumps(specification, indent=4, sort_keys=True))
    # create directories, download and preprocess articles
    for category in specification:
        directory = output / category['title']
        directory.mkdir(parents=True, exist_ok=True)
        for subcategory in category['subcategories']:
            subdirectory = directory / subcategory['title']
            subdirectory.mkdir(parents=True, exist_ok=True)
            for article in subcategory['articles']:
                filepath = subdirectory / article
                with filepath.open('w') as f:
                    print('Downloading {}'.format(filepath))
                    response = requests.get(REST_API + article)
                    f.write(response.text)


def iter_all_documents(input):
    for article in input.glob('./*/*/*'):
        print('Preprocessing {}'.format(article))
        with article.open() as f:
            tokens = tokenize(f.read())
        yield TaggedDocument(tokens, [str(article)])


def process(input):
    input = Path(input)
    documents = list(iter_all_documents(input))
    model = Doc2Vec(documents, vector_size=100, window=8, min_count=2, workers=7)  # noqa
    filepath = input / 'model.doc2vec.gz'
    model.save(str(filepath))


def guess(input, url):
    response = requests.get(url)
    string = response.text
    tokens = tokenize(string)
    model = Doc2Vec.load(str(Path(input) / 'model.doc2vec.gz'))
    vector = model.infer_vector(tokens)
    for doc, score in model.docvecs.most_similar([vector]):
        print('{} ~ {}'.format(doc, score))


if __name__ == '__main__':
    args = docopt(__doc__)
    if args.get('collect'):
        collect(args.get('OUTPUT'))
    elif args.get('process'):
        process(args.get('INPUT'))
    elif args.get('guess'):
        guess(args.get('INPUT'), args.get('URL'))

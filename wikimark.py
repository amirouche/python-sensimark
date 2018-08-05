#!/usr/bin/env python3
"""Usage:
  wikimark.py collect OUTPUT
  wikimark.py process INPUT
  wikimark.py guess [--all][--format=human|json] INPUT
  wikimark.py tool ngrams SIZE MIN INPUT
  wikimark.py tool html2paragraph INPUT
"""
import json
import pickle
import re
import sys
from collections import Counter
from collections import OrderedDict
from multiprocessing import Pool
from multiprocessing import cpu_count
from pathlib import Path
from string import punctuation
from urllib.parse import quote_plus


import requests
from asciitree import LeftAligned
from docopt import docopt
from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import Doc2Vec
from lxml import html
from lxml.html.clean import clean_html
from sklearn import svm


# lxml helper


def get_children(xml):
    """List children ignoring comments"""
    return [e for e in xml.iterchildren() if not isinstance(e, html.HtmlComment)]  # noqa


# html2paragraph

def extract_paragraphs(element):
    if element.tag == 'hr':
        return []
    if element.tag == 'p':
        text = clean_html(element).text_content()
        text = ' '.join(text.split())
        return [text]
    if element.tag[0] == 'h':
        text = clean_html(element).text_content()
        text = ' '.join(text.split())
        return [text]
    out = list()
    for child in get_children(element):
        out.extend(extract_paragraphs(child))
    return out


def html2paragraph(string):
    out = list()
    xml = html.fromstring(string)
    # extract title
    title = xml.xpath('/html/head/title/text()')[0]
    title = ' '.join(title.split())  # sanitize
    out.append(title)
    # extract the rest
    body = xml.xpath('/html/body')[0]
    out.extend(extract_paragraphs(body))
    return out


# core

REST_API = 'https://en.wikipedia.org/api/rest_v1/page/html/'
INPUT = REST_API + 'Wikipedia%3AVital_articles'


REGEX_TITLE = re.compile(r'[^(]+')


def tokenize(string):
    # strip punctuation
    clean = ''.join([' ' if c in punctuation else c for c in string]).split()
    # remove words smaller than 3
    tokens = [e for e in (' '.join(clean)).lower().split() if len(e) > 2]
    return tokens


def extract_subcategory(section):
    out = dict()
    children = get_children(section)
    # ignore some div at the end, that happens in Geography > General
    header, ul = children[0], children[1]
    title = header.xpath('./text()')[0]
    title = REGEX_TITLE.match(title).group().strip()
    out['title'] = title
    out['articles'] = list()
    for href in ul.xpath('.//a/@href'):
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
    output = Path(output)
    # write specification
    specification = get_specification()
    with (output / 'specification.json').open('w') as f:
        f.write(json.dumps(specification, indent=4, sort_keys=True))
    # create directories, download articles
    for category in specification:
        directory = output / category['title']
        directory.mkdir(parents=True, exist_ok=True)
        for subcategory in category['subcategories']:
            subdirectory = directory / subcategory['title']
            subdirectory.mkdir(parents=True, exist_ok=True)
            for article in subcategory['articles']:
                filename = quote_plus(article)
                filepath = subdirectory / filename
                with filepath.open('w') as f:
                    print('Downloading {}'.format(filepath))
                    response = requests.get(REST_API + article)
                    if response.status_code == 200:
                        f.write(response.text)


def iter_all_documents(input):
    for article in input.glob('./*/*/*'):
        print('Doc2Vec: Preprocessing "{}"'.format(article))
        with article.open() as f:
            string = f.read()
        for index, paragraph in enumerate(html2paragraph(string)):
            tokens = tokenize(paragraph)
            tag = '{} #{}'.format(article, index)
            yield TaggedDocument(tokens, [tag])


def make_dov2vec_model(input):
    documents = list(iter_all_documents(input))
    print('Doc2Vec: building the model')
    model = Doc2Vec(documents, vector_size=100, window=8, min_count=2, workers=7)  # noqa
    filepath = input / 'model.doc2vec.gz'
    model.save(str(filepath))
    return model


def iter_filepath_and_vectors(input, doc2vec):
    for filepath in input.glob('./*/*/*'):
        # skip the model, this is not an input document
        if filepath.name.endswith('.model'):
            continue
        #
        with filepath.open() as f:
            string = f.read()
        for index, paragraph in enumerate(html2paragraph(string)):
            tokens = tokenize(paragraph)
            yield filepath, doc2vec.infer_vector(tokens)


def regression(args):
    doc2vec, subcategory = args
    # skip models
    if not subcategory.is_dir():
        return
    # build regression model for the subcategory
    print('Building regression for "{}"'.format(subcategory))
    model = svm.SVR()
    X = list()
    y = list()
    input = subcategory.parent.parent
    for filepath, vector in iter_filepath_and_vectors(input, doc2vec):
        X.append(vector)
        value = 1. if filepath.parent == subcategory else 0.
        y.append(value)
    model.fit(X, y)
    with (subcategory / 'svr.model').open('wb') as f:
        pickle.dump(model, f)


def process(input):
    input = Path(input)
    print('Doc2Vec preprocessing')
    doc2vec = make_dov2vec_model(input)
    # doc2vec = Doc2Vec.load(str(input / 'model.doc2vec.gz'))
    print('Regression model computation')
    pool = Pool(cpu_count() - 1)
    subcategories = list(input.glob('./*/*/'))
    doc2vecs = [doc2vec] * len(subcategories)
    generator = pool.imap_unordered(regression, zip(doc2vecs, subcategories), chunksize=3)  # noqa
    for out in generator:
        pass


def guess(input, all_subcategories):
    input = Path(input)
    string = sys.stdin.read()
    doc2vec = Doc2Vec.load(str(input / 'model.doc2vec.gz'))
    subcategories = Counter()
    for index, paragraph in enumerate(html2paragraph(string)):
        tokens = tokenize(paragraph)
        vector = doc2vec.infer_vector(tokens)
        for filepath in input.glob('./*/*/*.model'):
            with filepath.open('rb') as f:
                model = pickle.load(f)
            prediction = model.predict([vector])[0]
            subcategories[filepath.parent] += prediction
    # compute the mean score for each subcategory
    for subcategory, prediction in subcategories.items():
        subcategories[subcategory] = prediction / (index + 1)
    # keep only the revelant categories
    total = len(subcategories) if all_subcategories else 10
    subcategories = OrderedDict(subcategories.most_common(total))
    # compute categories prediction
    categories = Counter()
    for category in input.glob('./*/'):
        # skip anything that is not a directory
        if not category.is_dir():
            continue
        # compute mean score for the category
        count = 0
        for subcategory, prediction in subcategories.items():
            if subcategory.parent == category:
                count += 1
                categories[category] += prediction
        if count:
            mean = categories[category] / count
            categories[category] = mean
        else:
            del categories[category]
    # build and print tree
    tree = OrderedDict()
    for category, prediction in categories.most_common(len(categories)):
        name = '{} ~ {}'.format(category.name, prediction)
        children = OrderedDict()
        for subcategory, prediction in subcategories.items():
            if subcategory.parent == category:
                children['{} ~ {}'.format(subcategory.name, prediction)] = dict()  # noqa
        tree[name] = children
    return dict(similarity=tree)


def file_ngrams(size, file):
    with file.open('r') as f:
        content = f.read()
    tokens = tokenize(content)
    grams = [tokens[i:i+size] for i in range(len(tokens) - size + 1)]
    grams = [' '.join(gram) for gram in grams]
    out = Counter(grams)
    return out


def ngrams(size, min, input):
    input = Path(input)
    if input.is_dir():
        out = Counter()
        for file in input.glob('./*'):
            if file.name.endswith('.model'):
                continue
            other = file_ngrams(size, file)
            out.update(other)
        items = sorted(out.items(), key=lambda x: x[1], reverse=True)
        for ngram, count in items:
            if count < min:
                break
            print('count("{}") == {}'.format(ngram, count))
    else:
        print('* Ngrams of size {} occurring at least {} in {}:'.format(
            size,
            min,
            input)
        )
        out = file_ngrams(size, input)
        items = sorted(out.items(), key=lambda x: x[1], reverse=True)
        for ngram, count in items:
            if count < min:
                break
            print('** count("{}") == {}'.format(ngram, count))



if __name__ == '__main__':
    args = docopt(__doc__)
    # print(args)
    if args.get('collect'):
        collect(args.get('OUTPUT'))
    elif args.get('process'):
        out = process(args.get('INPUT'))
    elif args.get('guess'):
        out = guess(args.get('INPUT'), args.get('--all', False))
        switch = args.get('--format', 'human') or 'human'
        if switch == 'human':
            print(LeftAligned()(out))
        elif switch == 'json':
            print(json.dumps(out, indent=True))
        else:
            RuntimeError('Something requires amirouche code assistance https://github.com/amirouche/sensimark?')
    elif args.get('tool') and args.get('ngrams'):
        ngrams(int(args.get('SIZE')), int(args.get('MIN')), args.get('INPUT'))
    elif args.get('tool') and args.get('html2paragraph'):
        input = Path(args.get('INPUT'))
        with input.open() as f:
            out = html2paragraph(f.read())
            print(json.dumps(out, indent=True))
    else:
        raise Exception('Some command is not handled properly')

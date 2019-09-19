#!/usr/bin/env python3
"""Usage:
  wikimark.py collect OUTPUT
  wikimark.py fasttext prepare INPUT OUTPUT
  wikimark.py fasttext train INPUT OUTPUT
  wikimark.py fasttext estimate INPUT
  wikimark.py v1 train INPUT
  wikimark.py v1 estimate [--all][--format=human|json] INPUT
  wikimark.py v2 prepare INPUT OUTPUT
  wikimark.py v2 train INPUT
  wikimark.py v2 estimate INPUT
  wikimark.py v3 train INPUT
  wikimark.py v3 estimate INPUT
  wikimark.py tool ngrams SIZE MIN INPUT
  wikimark.py tool html2paragraph INPUT
  wikimark.py tool vital2orgmode
"""
import json
import logging
import pickle
import re
import sys
from collections import Counter
from collections import OrderedDict
from functools import lru_cache
from multiprocessing import Pool
from multiprocessing import cpu_count
from pathlib import Path
from string import punctuation
from urllib.parse import quote_plus

import daiquiri
import requests
from asciitree import LeftAligned
from docopt import docopt
from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import Doc2Vec
from lxml import html
from lxml.html.clean import clean_html
from sklearn import svm
from sklearn import preprocessing
import snowballstemmer
from wordfreq import top_n_list


daiquiri.setup(level=logging.INFO, outputs=("stderr",))
log = logging.getLogger(__name__)

stem = snowballstemmer.stemmer("english").stemWord
GARBAGE_TO_SPACE = dict.fromkeys((ord(x) for x in punctuation), " ")
STOP_WORDS = set(top_n_list("en", 800))


WORD_MIN_LENGTH = 2
WORD_MAX_LENGTH = 64  # sha2 length


def sane(word):
    return WORD_MIN_LENGTH <= len(word) <= WORD_MAX_LENGTH


def string2words(string):
    """Converts a string to a list of words.

    Removes punctuation, lowercase, words strictly smaller than 2 and strictly bigger than 64
    characters

    Returns a set.
    """
    clean = string.translate(GARBAGE_TO_SPACE).lower()
    words = set(word for word in clean.split() if sane(word))
    return words


def tokenize(string):
    words = string2words(string)
    tokens = [stem(word) for word in words if word not in STOP_WORDS]
    return tokens


# lxml helper

def get_children(xml):
    """List children ignoring comments"""
    return [e for e in xml.iterchildren() if not isinstance(e, html.HtmlComment)]  # noqa


# vital2orgmode

def skip(href):
    if not href.startswith('/wiki/'):
        return True
    if href.startswith('/wiki/Wikipedia:'):
        return True
    if href.startswith('/wiki/User:'):
        return True
    if href.startswith('/wiki/Template:'):
        return True
    if href.startswith('/wiki/Template_talk:'):
        return True
    if href.startswith('/wiki/Portal:'):
        return True
    if href.startswith('/wiki/Special:'):
        return True



def _vital2orgmode(node):
    if isinstance(node, html.HtmlComment):
        return
    elif node.tag[0] == 'h':
        level = int(node.tag[1])
        prefix = '*' * level
        text = node.text_content().strip().replace('[edit]', '')
        if text == 'Contents':
            return
        try:
            parens = text.index('(')
        except ValueError:
            pass
        else:
            text = text[:parens]
        msg = '{} {}'.format(prefix, text)
        print(msg)
    elif node.tag == 'a':
        if node.attrib.get('href') is None:
            return
        href = node.attrib['href']
        if skip(href):
            return
        msg = "******* {}{}".format(REST_API, href[6:])
        print(msg)
    else:
        for child in node.iterchildren():
            _vital2orgmode(child)


def vital2orgmode(string):
    """Convert vital hierarchy to orgmode file."""
    body = html.fromstring(string).xpath('//div[@id="mw-content-text"]')[0]
    _vital2orgmode(body)


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


@lru_cache(maxsize=None)
def filepath2paragraphs_of_tokens(filepath):
    log.debug('filepath2paragraphs_of_tokens: %s', filepath)
    with filepath.open() as f:
        paragraphs = html2paragraph(f.read())
    out = [tokenize(p) for p in paragraphs]
    return out


def filepath2paragraphs(filepath):
    log.info('filepath2paragraphs: %s', filepath)
    with filepath.open() as f:
        out = html2paragraph(f.read())
    return out


# core

REST_API = 'https://en.wikipedia.org/api/rest_v1/page/html/'
INPUT = REST_API + 'Wikipedia%3AVital_articles'


REGEX_TITLE = re.compile(r'[^(]+')


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
    for filepath in input.glob('./*/*/*'):
        log.debug('Doc2Vec: Preprocessing "{}"'.format(filepath))
        if str(filepath).endswith('.model'):
            continue
        for index, tokens in enumerate(filepath2paragraphs_of_tokens(filepath)):
            tag = '{} #{}'.format(filepath, index)
            yield TaggedDocument(tokens, [tag])


def make_doc2vec_model(input):
    filepath = input / 'doc2vec.model'
    if filepath.is_file():
        log.warning('Loading previous doc2vec.model: %s', filepath)
        out = Doc2Vec.load(str(filepath))
        return out
    else:
        documents = list(iter_all_documents(input))
        log.info('Doc2Vec: building the model')
        out = Doc2Vec(documents, vector_size=300, window=8, min_count=2, workers=5)  # noqa
        out.save(str(filepath))
        return out


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
    model = svm.SVR(gamma='scale')
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


def train(input):
    input = Path(input)
    print('doc2vec training')
    doc2vec = make_doc2vec_model(input)
    print('Regression model computation')
    pool = Pool(cpu_count() - 2)
    subcategories = list(input.glob('./*/*/'))
    doc2vecs = [doc2vec] * len(subcategories)
    generator = pool.imap_unordered(regression, zip(doc2vecs, subcategories), chunksize=3)  # noqa
    for out in generator:
        pass


def estimate(input, all_subcategories):
    input = Path(input)
    string = sys.stdin.read()
    doc2vec = Doc2Vec.load(str(input / 'doc2vec.model'))
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


# fast text

def fasttext_iter_all_documents(input):
    import syntok.segmenter as segmenter
    for article in input.glob('./*/*/*'):
        label = '__label__' + '-'.join(tokenize('-'.join(str(article).split('/')[1:3])))
        print('* handling {} for {}'.format(article, label))

        with article.open() as f:
            string = f.read()
        paragraphs = '\n\n'.join(html2paragraph(string))
        paragraphs = segmenter.process(paragraphs)
        for paragraph in paragraphs:
            for sentence in paragraph:
                sentence = ' '.join(token.value for token in sentence)
                yield label, sentence


def fasttext_prepare(input, output):
    with Path(output).open('w') as f:
        for label, phrase in fasttext_iter_all_documents(Path(input)):
            f.write('{} {}\n'.format(label, phrase))


def fasttext_train(input, output):
    import fastText as ft
    model = ft.train_supervised(input=input, dim=300, pretrainedVectors='wiki-news-300d-1M-subword.vec')
    model.save_model(output)

def fasttext_estimate(input):
    import fastText as ft
    import syntok.segmenter as segmenter
    model = ft.load_model(input)
    string = string = sys.stdin.read()
    paragraphs = '\n\n'.join(html2paragraph(string))
    paragraphs = segmenter.process(paragraphs)
    counter = Counter()
    for paragraph in paragraphs:
        for sentence in paragraph:
            sentence = ' '.join(token.value for token in sentence)
            out = model.predict(sentence, 73)  # number of labels
            out = {out[0][i]: out[1][i] for i in range(73)}
            counter = counter + Counter(out)
    for key, value in counter.most_common(10):
        print('{}\t\t{}'.format(key, value))


def v2_train(path):
    # from sklearn.model_selection import train_test_split
    from sklearn.linear_model import SGDClassifier
    input = output = Path(path).resolve()
    log.info('doc2vec training')
    doc2vec = make_doc2vec_model(input)
    log.info('infer vectors')  # TODO: Pool.map ordered
    nodes = sorted(list(input.glob('./**/')))
    X, y = [], []
    log.info('There is %r nodes...', len(nodes))
    for index, node in enumerate(nodes):
        filepaths = node.glob('./**/*')
        for filepath in filepaths:
            if '.model' in str(filepath):
                continue
            if filepath.is_dir():
                continue
            log.debug('infer vectors for: %s', filepath)
            paragraphs = filepath2paragraphs_of_tokens(filepath)
            for tokens in paragraphs:
                vector = doc2vec.infer_vector(tokens)
                X.append(vector)
                y.append(index)
    #
    log.info('train global estimator')
    # train the estimator on all nodes aka. global_estimator
    global_estimator = SGDClassifier(loss="log", penalty="l2", max_iter=5)
    X_scaled = preprocessing.scale(X)
    global_estimator.fit(X, y)
    with (output / 'global.model').open('wb') as f:
        pickle.dump(global_estimator, f)

    # XXX: THIS IS GARBAGE
    # log.critical('train leaf estimator')
    # # train estimator score of leaf nodes aka. leaf_estimator
    # X_leaf_estimator = []
    # X_train_leaf_estimations = global_estimator.predict_proba(X_train_leaf)
    # leaf_estimator = SGDClassifier(loss="log", penalty="l2", max_iter=5)
    # leaf_estimator.fit(X_train_leaf_estimations, y_train_leaf)
    # with (output / 'leaf.model').open('wb') as f:
    #     pickle.dump(leaf_estimator, f)


def v2_estimate(input):
    input = Path(input).resolve()
    log.info('Infering vectors of html input on stdin...')
    string = sys.stdin.read()
    doc2vec = make_doc2vec_model(input)
    paragraphs = html2paragraph(string)
    vectors = []
    for index, paragraph in enumerate(paragraphs):
        tokens = tokenize(paragraph)
        vector = doc2vec.infer_vector(tokens)
        vectors.append(vector)
    log.info('Loading models.')
    with (input / 'global.model').open('rb') as f:
        global_estimator = pickle.load(f)
    # with (input / 'leaf.model').open('rb') as f:
    #     leaf_estimator = pickle.load(f)
    nodes = sorted(list(input.glob('./**/')))
    log.critical('There is %r nodes...', len(nodes))
    log.info('Global estimation...')
    global_estimations = global_estimator.predict_proba(vectors)
    # XXX: THIS IS GARBAGE TOO
    #for estimation in global_estimations:
    #    log.critical('global: %r', len(estimation))
    #log.info('Leaf estimation...')
    #leaf_estimations = leaf_estimator.predict_proba(global_estimations)
    log.info('Checkout each index score')
    counter = Counter()
    for estimation in global_estimations:
        new = Counter(dict(list(enumerate(estimation))))
        counter = counter + new
    log.info('Checkout each filepath score')
    scores = Counter()
    for index, score in counter.items():
        filepath = nodes[index]
        scores[filepath] = score
    subcategories = Counter()
    #
    for subcategory in input.glob('./*/*/') :
        subcategories[subcategory] = scores[subcategory]
    # keep only the revelant categories
    # total = len(subcategories) if all_subcategories else 10
    total = 10 # len(subcategories)
    subcategories = OrderedDict(subcategories.most_common(total))
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
            categories[category] = scores[category]
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
    out = dict(similarity=tree)
    print(LeftAligned()(out))




def v3_train(path):
    import spacy
    from sklearn.linear_model import SGDClassifier
    input = output = Path(path).resolve()
    log.info('spacy init')
    nlp = spacy.load('en_core_web_lg')
    log.info('infer vectors')
    nodes = sorted(list(input.glob('./**/')))
    X, y = [], []
    log.info('There is %r nodes...', len(nodes))
    for index, node in enumerate(nodes):
        filepaths = node.glob('./**/*')
        for filepath in filepaths:
            if '.model' in str(filepath):
                continue
            if filepath.is_dir():
                continue
            log.debug('infer vectors for: %s', filepath)
            paragraphs = filepath2paragraphs(filepath)
            for paragraph in paragraphs:
                paragraph = nlp(paragraph)
                X.append(filepath)
                y.append(paragraph.vector)
    log.info('train global estimator')
    # train the estimator on all nodes aka. global_estimator
    global_estimator = SGDClassifier(loss="log", penalty="l2", max_iter=5)
    global_estimator.fit(X, y)
    with (output / 'global.model').open('wb') as f:
        pickle.dump(global_estimator, f)


if __name__ == '__main__':
    args = docopt(__doc__)
    # print(args)

    if args.get('collect'):
        collect(args.get('OUTPUT'))
    elif args.get('fasttext'):
        if args.get('prepare'):
            fasttext_prepare(args.get('INPUT'), args.get('OUTPUT'))
        if args.get('train'):
            fasttext_train(args.get('INPUT'), args.get('OUTPUT'))
        if args.get('estimate'):
            fasttext_estimate(args.get('INPUT'))
    elif args.get('v1'):
        if args.get('train'):
            out = train(args.get('INPUT'))
        elif args.get('estimate'):
            out = estimate(args.get('INPUT'), args.get('--all', False))
            switch = args.get('--format', 'human') or 'human'
            if switch == 'human':
                print(LeftAligned()(out))
            elif switch == 'json':
                print(json.dumps(out, indent=True))
            else:
                RuntimeError('Something requires assistance https://github.com/amirouche/sensimark?')
    elif args.get('v3'):
        if args.get('train'):
            v3_train(args.get('INPUT'))
    elif args.get('v2'):
        if args.get('prepare'):
            v2_prepare(args.get('INPUT'), args.get('OUTPUT'))
        if args.get('train'):
            v2_train(args.get('INPUT'))
        if args.get('estimate'):
            v2_estimate(args.get('INPUT'))
    elif args.get('tool') and args.get('ngrams'):
        ngrams(int(args.get('SIZE')), int(args.get('MIN')), args.get('INPUT'))
    elif args.get('tool') and args.get('html2paragraph'):
        input = Path(args.get('INPUT'))
        with input.open() as f:
            out = html2paragraph(f.read())
            print(json.dumps(out, indent=True))
    elif args.get('tool') and args.get('vital2orgmode'):
        string = sys.stdin.read()
        vital2orgmode(string)
    else:
        raise Exception('Programming error: some command is not handled properly')

import pickle
from pathlib import Path
from collections import Counter
from multiprocessing import Pool

from gensim.models.doc2vec import Doc2Vec

from wikimark import html2paragraph
from wikimark import tokenize

doc2vec = None
regressions = None


def process(filepath):
    global doc2vec, regressions
    with filepath.open('r') as f:
        string = f.read()
    subcategories = Counter()
    for index, paragraph in enumerate(html2paragraph(string)):
        tokens = tokenize(paragraph)
        vector = doc2vec.infer_vector(tokens)
        for subcategory, model in regressions.items():
            prediction = model.predict([vector])[0]
            subcategories[subcategory] += prediction
    # compute the mean score for each subcategory
    for subcategory, prediction in subcategories.items():
        subcategories[subcategory] = prediction / (index + 1)
    # keep only the main category
    subcategory = subcategories.most_common(1)[0]
    return (filepath, subcategory)


def main():
    global doc2vec, regressions
    input = Path('./build')
    doc2vec = Doc2Vec.load(str(input / 'model.doc2vec.gz'))
    regressions = dict()
    for filepath in input.glob('./*/*/*.model'):
        with filepath.open('rb') as f:
            model = pickle.load(f)
        regressions[filepath.parent] = model

    examples = list(input.glob('../data/wikipedia/english/*'))

    with Pool() as pool:
        for filepath, subcategory in pool.imap_unordered(process, examples):
            print('* {} -> {}'.format(filepath, subcategory))


if __name__ == '__main__':
    main()

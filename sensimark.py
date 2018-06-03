import re
import logging
import math
import pickle
from pathlib import Path
from collections import Counter
from collections import OrderedDict

from aiohttp import ClientSession
from aiohttp import web
from gensim.models.doc2vec import Doc2Vec
from setproctitle import setproctitle
from wikimark import html2paragraph
from wikimark import tokenize


log = logging.getLogger()


REGEX_URL = re.compile(
    r'^(?:http|ftp)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE
)


async def status(request):
    return web.json_response({'status': 'ok'})


async def v0(request):
    # validate all
    all = request.query.get('all', False)
    # validate url
    try:
        url = request.query['url']
    except KeyError:
        data = dict(
            status='validation error',
            message='missing url parameter in query string'
        )
        return web.json_response(data, status=400)
    if re.match(REGEX_URL, url) is None:
        data = dict(
            status='validation error',
            message='malformated url parameter'
        )
        return web.json_response(data, status=400)

    # validate top
    top = request.query.get('top', 5)
    try:
        top = int(top)
    except ValueError:
        data = dict(
            status='validation error',
            message='top is not a number'
        )
        return web.json_response(data, status=400)

    # proceed

    # fetch the page
    async with request.app['session'].get(url) as response:
        string = await response.text()

    # compute predictions
    subcategories = Counter()
    doc2vec = request.app['doc2vec']
    regressions = request.app['regressions']
    for index, paragraph in enumerate(html2paragraph(string)):
        tokens = tokenize(paragraph)
        vector = doc2vec.infer_vector(tokens)
        for subcategory, model in regressions.items():
            prediction = model.predict([vector])[0]
            subcategories[subcategory] += prediction
    # compute the mean score for each subcategory
    for subcategory, prediction in subcategories.items():
        # magic
        value = math.exp(prediction / (index + 1))
        magic = ((value * 100) - 110) * 100
        subcategories[subcategory] = magic

    total = len(subcategories) if all else top
    subcategories = OrderedDict(subcategories.most_common(total))
    # compute categories prediction
    categories = Counter()
    input = Path('./build/')
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
    # build tree
    tree = OrderedDict()
    for category, prediction in categories.most_common(len(categories)):
        name = '{} ~ {}'.format(category.name, prediction)
        item_category = dict(
            name=category.name,
            prediction=prediction
        )
        children = OrderedDict()
        for subcategory, prediction in subcategories.items():
            if subcategory.parent == category:
                item_subcategory = dict(
                    name=subcategory.name,
                    prediction=prediction,
                )
                children[subcategory.name] = item_subcategory
        item_category['children'] = list(children.values())
        tree[name] = item_category
    # build output as a list to keep ordering
    out = list()
    for category in tree.values():
        out.append(category)
    # win!
    return web.json_response(out)


# boot the app

def create_app(loop):
    """Starts the aiohttp process to serve the REST API"""
    setproctitle('sensimark-api')
    log.debug("boot")

    # init app
    app = web.Application()  # pylint: disable=invalid-name
    app['session'] = ClientSession()
    # init models

    input = Path('./build')
    app['doc2vec'] = Doc2Vec.load(str(input / 'model.doc2vec.gz'))
    app['regressions'] = regressions = dict()
    for filepath in input.glob('./*/*/*.model'):
        with filepath.open('rb') as f:
            model = pickle.load(f)
        regressions[filepath.parent] = model

    # routes
    app.router.add_routes([
        web.get('/api/status', status),
        web.get('/api/v0', v0)
    ])

    return app

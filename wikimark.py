#!/usr/bin/env python3
"""Usage:
  wikimark.py collect OUTPUT
  wikimark.py process INPUT
  wikimark.py guess INPUT
"""
import json
import re
from pathlib import Path

import requests

from lxml import html
from docopt import docopt

REST_API = 'https://en.wikipedia.org/api/rest_v1/page/html/'
INPUT = REST_API + 'Wikipedia%3AVital_articles'


REGEX_TITLE = re.compile(r'[^(]+')


def get_children(xml):
    """List children ignoring comments"""
    return [e for e in xml.iterchildren() if not isinstance(e, html.HtmlComment)]

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
        if href not in ("Wikipedia:Vital_articles/Level/2", "Wikipedia:Vital_articles/Level/1"):
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


if __name__ == '__main__':
    args = docopt(__doc__)
    if args.get('collect'):
        collect(args.get('OUTPUT'))

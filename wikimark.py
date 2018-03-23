#!/usr/bin/env python3
"""Usage:
  wikimark.py download OUTPUT
  wikimark.py process INPUT
  wikimark.py guess INPUT
"""
import json
import re

import requests

from lxml import html
from docopt import docopt

INPUT = 'https://en.wikipedia.org/api/rest_v1/page/html/Wikipedia%3AVital_articles'


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
    out['subcategory'] = list()
    for h3 in div.xpath('.//h3'):
        # for mathematics, the above xpath doesn't work skip it, see
        # the talk page for more info
        section = h3.getparent()
        subcategory = extract_subcategory(section)
        out['subcategory'].append(subcategory)
    return out


def download(output):
    response = requests.get(INPUT)
    xml = html.fromstring(response.text)
    section = xml.xpath('body/section[@data-mw-section-id=1]')[0]
    children = get_children(section)
    assert len(children) == 14, "the html changed, update the code"
    sections = children[3:]
    categories = [extract_category(section) for section in sections]
    return categories


if __name__ == '__main__':
    args = docopt(__doc__)
    if args.get('download'):
        print(json.dumps(download(args.get('OUTPUT')), indent=4, sort_keys=True))
    else:
        pass

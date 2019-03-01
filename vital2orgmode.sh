#!/bin/sh
curl $1 | wikimark.py tool vital2orgmode > "$(basename $1).org"

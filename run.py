#!/usr/bin/env python3
import asyncio
import argparse

from aiohttp import web

from sensimark import create_app


parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--port')
parser.add_argument('--path')


if __name__ == '__main__':
    args = parser.parse_args()
    app = create_app(asyncio.get_event_loop())
    web.run_app(app, path=args.path, port=args.port)

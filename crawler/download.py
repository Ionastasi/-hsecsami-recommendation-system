#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

'''
вынести htmls в main (когда он появится)
'''

from html.parser import HTMLParser
import urllib.request
import os
from datetime import date
import signal

import log
from config import *


LINK_PREFIX_POST = "http://geektimes.ru/post/"
LINK_PREFIX_ALL_PAGE = "http://geektimes.ru/all/page"

htmls = set(map(int, open(HTMLS_INDEX).readlines()))


class ParserPageAll(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._posts = list()


    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            attrs = dict(attrs)
            if 'class' in attrs :
                if 'post ' in attrs['class'] and 'shortcuts_item' in attrs['class']:
                # 'post shortcuts_item', 'post translation shortcuts_item', may be smth else
                # and it can't be 'posts shortcuts_item'
                    self._posts.append(int(attrs['id'].replace('post_', '')))  # post_271508 -> 271508


    def parse(self, page):
        self.feed(page)
        return self._posts


def download(url, bad_NotFound=False):
    try:
        response = urllib.request.urlopen(url)
        log.debug('Load "{}"... {} {}'.format(url, response.reason, response.getcode()))

    except (urllib.error.URLError, urllib.error.HTTPError) as exception:
        if exception.code == 404 and not bad_NotFound:
            log.debug('Load "{}"... {} {}'.format(url, exception.reason, exception.code))
        else:
            log.error('Load "{}"... {} {}'.format(url, exception.reason, exception.code))

    else:
        return response.read().decode('utf-8')


def download_post(url):
    text = download(url)
    if not text:
        return
    id_page = url.replace(LINK_PREFIX_POST, '')
    path = '{}.html'.format(DIR_HTML + id_page)
    today = date.today().isoformat()  # i should know it when parsing page
    with open(path, 'w') as fout:
        fout.write("<!-- when_downloaded {} -->\n{}".format(today, text))
    log.debug('Store {} to {}... {} KB'.format(url, path, round(os.path.getsize(path) // KB_SIZE)))


def download_last(print_ids=False, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt
    for page_n in range(1, 101):
        url = LINK_PREFIX_ALL_PAGE + str(page_n)
        text = download(url, bad_NotFound=True)
        for post_id in ParserPageAll().parse(text):
            if force or post_id not in htmls:
                download_post(LINK_PREFIX_POST + str(post_id))
                htmls.add(post_id)
                if print_ids:
                    print(post_id)
    ending()

def download_range(first, last, print_ids=False, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt
    first, last = min(first, last), max(first, last)
    for post_id in range(first, last + 1):
        if force or post_id not in htmls:
            download_post(LINK_PREFIX_POST + str(post_id))
            htmls.add(post_id)
            if print_ids:
                print(post_id)
    ending()


def ending():
    with open(HTMLS_INDEX, 'w') as fout:
        fout.write('\n'.join(map(str, htmls)))


def signal_handler(signal, frame):
    ending()
    exit()

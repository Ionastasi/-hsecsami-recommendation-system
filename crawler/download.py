#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
import urllib.request
import os
from datetime import date
import signal

import log


KB_SIZE = 1024
DIR_HTML = '../data/html/'
HTMLS_INDEX = '../data/html/.index'
LINK_PREFIX_POST = "http://geektimes.ru/post/"
LINK_PREFIX_ALL_PAGE = "http://geektimes.ru/all/page"

htmls = set(map(int, open(HTMLS_INDEX).readlines()))


class Parser_page_all(HTMLParser):  # posts from all-page
    def __init__(self):
        HTMLParser.__init__(self)
        self.posts = list()


    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            attrs = dict(attrs)
            if 'class' in attrs :
                if 'post ' in attrs['class'] and 'shortcuts_item' in attrs['class']:
                # 'post shortcuts_item', 'post translation shortcuts_item', may be smth else
                # and it can't be 'posts shortcuts_item'
                    self.posts.append(int(attrs['id'].replace('post_', '')))  # post_271508 -> 271508


    def parse(self, page):
        self.feed(page)
        return self.posts


def download(url):
    try:
        response = urllib.request.urlopen(url)
        log.debug('Load "{}"... {} {}'.format(url, response.reason, response.getcode()))

    except (urllib.error.URLError, urllib.error.HTTPError) as exception:
        if exception.code == 404:  # debug
            log.debug('Load "{}"... {} {}'.format(url, exception.reason, exception.code))
        else:                      # error
            log.error('Load "{}"... {} {}'.format(url, exception.reason, exception.code))

    else:
        return response


def download_post(url):
    response = download(url)
    if not response:
        return
    id_page = url.replace(LINK_PREFIX_POST, '')
    path = '{}.html'.format(DIR_HTML + id_page)
    text = response.read().decode('utf-8')
    today = date.today().isoformat()  # i should know it when parsing page
    with open(path, 'w') as fout:
        fout.write("<!-- when_downloaded {} -->\n{}".format(today, text))
    log.debug('Store {} to {}... {} KB'.format(url, path, round(os.path.getsize(path) // KB_SIZE)))


def download_last(print_ids=False, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt
    for p in range(1, 101):
        url = LINK_PREFIX_ALL_PAGE + str(p)
        response = download(url)
        text = response.read().decode('utf-8')
        for post in Parser_page_all().parse(text):
            if force or post not in htmls:
                download_post(LINK_PREFIX_POST + str(post))
                htmls.add(post)
                if print_ids:
                    print(post)
    ending()

def download_range(first, last, print_ids=False, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt
    for post in range(first, last + 1):
        if force or post not in htmls:
            download_post(LINK_PREFIX_POST + str(post))
            htmls.add(post)
            if print_ids:
                print(post)
    ending()


def ending():
    with open(HTMLS_INDEX, 'w') as fout:
        fout.write('\n'.join(map(str, htmls)))


def signal_handler(signal, frame):
    ending()
    exit()

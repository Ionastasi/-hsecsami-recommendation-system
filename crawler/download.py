#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
import urllib.request
import os
from datetime import date


import log


DIR_HTML = '../data/html/'
LINK_PREFIX_POST = "http://geektimes.ru/post/"
LINK_PREFIX_ALL_PAGE = "http://geektimes.ru/all/page"
HTMLS_INDEX = '../data/html/.index'
KB_SIZE = 1024


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


def downloaded_html_files():
    # 271508.html -> 271508
    flist = set(map(int, open(HTMLS_INDEX).readlines()))
    return flist


def download(url):
    try:
        response = urllib.request.urlopen(url)
        log.debug('Load "{}"... {} {}'.format(url, response.reason, response.getcode()))

    except (urllib.error.URLError, urllib.error.HTTPError) as exception:
        if exception.code == 404:
            log.debug('Load "{}"... {} {}'.format(url, exception.reason, exception.code))
        else:
            log.error('Load "{}"... {} {}'.format(url, exception.reason, exception.code))

    else:
        return response


def download_post(url):
    response = download(url)
    id_page = url.replace(LINK_PREFIX_POST, '')
    path = '{}.html'.format(DIR_HTML + id_page)
    text = response.read().decode('utf-8')
    today = date.today().strftime('%y.%m.%d')  # i should know it when parsing page
    with open(path, 'w') as fout:
        fout.write("<!-- when_downloaded {} -->\n{}".format(today, text))
    with open(HTMLS_INDEX, 'a') as fout:
        fout.write('{}\n'.format(id_page))
    log.debug('Store {} to {}... {} KB'.format(url, path, round(os.path.getsize(path) // KB_SIZE)))


def download_last():
    htmls = downloaded_html_files()
    for p in range(1, 101):
        url = '{}{}/'.format(LINK_PREFIX_ALL_PAGE, p)
        response = download(url)
        text = response.read().decode('utf-8')
        for post in Parser_page_all().parse(text):
            if post not in htmls:
                download_post('{}{}'.format(LINK_PREFIX_POST, post))


def download_range(first, last):
    htmls = downloaded_html_files()
    for post in range(first, last + 1):
        if post not in htmls:
            download_post('{}{}'.format(LINK_PREFIX_POST, post))
